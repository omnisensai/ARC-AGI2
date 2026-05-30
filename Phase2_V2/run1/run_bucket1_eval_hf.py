"""Bucket 1 eval using plain transformers + PEFT (no vLLM).

Slower than vLLM (sequential generation) but no dep version hell — uses the
same transformers/peft/torch that axolotl trained with, no extra installs.

Expected runtime: ~15-25 min for 100 puzzles on H100 (sequential greedy
generation, max_new_tokens=2048 with early-stop on EOS).

Usage:
    python3 Phase2_V2/run1/run_bucket1_eval_hf.py \\
        --lora outputs/phase2_v2_run1/checkpoint-2460 \\
        [--limit N]    # cap puzzles for quick smoke test

Writes Phase2_V2/run1/eval/bucket1.jsonl.
"""
import argparse, ast, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
P2 = REPO / "Phase2_V2"
sys.path.insert(0, str(P2 / "micro"))
sys.path.insert(0, str(P2 / "scripts"))

# EXACT same SYSTEM and renderer used at training time
from build_micro_sft import SYSTEM, render_pairs
from canonical_gate import audit as _ast_audit


def load_puzzle(pid):
    """Load puzzle from the SAME source training used (canonical/ground_truth_puzzles/).

    The other location Phase2_V2/Puzzle_Database/<pid>_*.json contains some
    files in a corrupted flattened 90x1 format that does NOT match training.
    Always use ground_truth_puzzles/ for eval to match the training distribution.
    """
    p = P2 / "canonical" / "ground_truth_puzzles" / f"{pid}.json"
    if p.exists():
        return json.loads(p.read_text())
    raise FileNotFoundError(f"no puzzle file for {pid} in canonical/ground_truth_puzzles/")


def build_prompt(puzzle):
    return SYSTEM, render_pairs(puzzle["train"]) + "\n\nWrite def solve(input_grid)."


def extract_code(text):
    s = text.strip()
    if "```" in s:
        chunks, cur, in_block = [], [], False
        for line in s.split("\n"):
            if line.startswith("```"):
                if in_block:
                    chunks.append("\n".join(cur)); cur = []
                in_block = not in_block
                continue
            if in_block: cur.append(line)
        if cur: chunks.append("\n".join(cur))
        if chunks: s = max(chunks, key=len)
    return s


def run_code(code, test_input, timeout=3.0):
    runner = (
        f"import sys, json\n"
        f"code = {code!r}\n"
        f"ns = {{}}\n"
        f"try:\n"
        f"    exec(code, ns)\n"
        f"    solve = ns.get('solve')\n"
        f"    if solve is None: raise RuntimeError('no solve function')\n"
        f"    inp = json.loads(sys.stdin.read())\n"
        f"    out = solve(inp)\n"
        f"    print('OK'); print(json.dumps(out))\n"
        f"except Exception as e:\n"
        f"    print('ERR'); print(type(e).__name__ + ': ' + str(e))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", runner],
            input=json.dumps(test_input),
            capture_output=True, text=True, timeout=timeout,
        )
        lines = result.stdout.split("\n", 1)
        if lines[0].strip() == "OK":
            return {"ok": True, "output": json.loads(lines[1]), "error": None}
        return {"ok": False, "output": None,
                "error": lines[1] if len(lines) > 1 else result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": None, "error": "TIMEOUT"}


def classify(code, run_result, expected, expected_shape):
    if not code or "def solve" not in code:
        return "EMPTY_OR_INVALID"
    try:
        ast.parse(code)
    except SyntaxError:
        return "EMPTY_OR_INVALID"
    flags = _ast_audit(code, big_literal_max=12)
    if flags and run_result["ok"] and run_result["output"] == expected:
        return "HARDCODED"
    if not run_result["ok"]:
        return "TIMEOUT" if run_result["error"] == "TIMEOUT" else "RUNTIME_ERROR"
    out = run_result["output"]
    if not isinstance(out, list) or not out or not isinstance(out[0], list):
        return "EMPTY_OR_INVALID"
    out_shape = (len(out), len(out[0]))
    if out_shape != expected_shape:
        return "SHAPE_MISMATCH"
    if out == expected:
        return "PASS"
    return "WRONG_OUTPUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True)
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.5,
                    help="generation temperature; 0.5 = mild sampling (default), "
                         "0.0 = greedy (deterministic but brittle to backend drift)")
    ap.add_argument("--num-beams", type=int, default=1,
                    help="beam search width; >1 overrides temperature. Catches "
                         "bad-token cascades that pure greedy can't recover from. "
                         "Recommended: 4")
    ap.add_argument("--repetition-penalty", type=float, default=1.0,
                    help="penalize already-emitted tokens (1.0 = off). >1 helps "
                         "with repetition collapse but hurts code legitimate "
                         "repetition (def X, def Y all share patterns)")
    ap.add_argument("--no-repeat-ngram", type=int, default=0,
                    help="forbid any N-gram from repeating (0 = off). For code, "
                         "tends to be too aggressive — boilerplate legitimately "
                         "repeats. Only enable if you see specific n-gram loops.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    out_path = Path(a.out or P2 / "run1/eval/bucket1.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ids = (P2 / "run1/splits/bucket1_trained_sample.txt").read_text().split()
    if a.limit:
        ids = ids[:a.limit]
    print(f"loading {len(ids)} puzzles ...")
    puzzles = {pid: load_puzzle(pid) for pid in ids}

    # === Load model + LoRA ===
    print(f"loading {a.base_model} (will take ~30s)...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    # Disable cuDNN SDPA backend (vLLM install bumped CUDA libs and broke cuDNN
    # ABI compatibility; eager / math kernels still work).
    torch.backends.cuda.matmul.allow_tf32 = True
    try:
        torch.backends.cuda.enable_cudnn_sdp(False)
    except Exception:
        pass
    try:
        torch.backends.cuda.enable_flash_sdp(False)
    except Exception:
        pass

    tokenizer = AutoTokenizer.from_pretrained(a.base_model)
    base = AutoModelForCausalLM.from_pretrained(
        a.base_model,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="eager",   # plain PyTorch attention; bypasses cuDNN
    )
    print(f"loading LoRA adapter from {a.lora} ...")
    model = PeftModel.from_pretrained(base, a.lora)
    model.eval()
    print("ready.")

    # === Generate + verify sequentially ===
    counts = {}
    t0 = time.time()
    with out_path.open("w") as fh:
        for i, pid in enumerate(ids, 1):
            puz = puzzles[pid]
            system, user = build_prompt(puz)
            prompt = tokenizer.apply_chat_template(
                [{"role": "system", "content": system},
                 {"role": "user", "content": user}],
                tokenize=False, add_generation_prompt=True,
            )
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            common = dict(
                max_new_tokens=a.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=a.repetition_penalty,
                no_repeat_ngram_size=a.no_repeat_ngram,
            )
            with torch.no_grad():
                if a.num_beams > 1:
                    output = model.generate(**inputs, **common,
                        do_sample=False, num_beams=a.num_beams, early_stopping=True)
                elif a.temperature > 0:
                    output = model.generate(**inputs, **common,
                        do_sample=True, temperature=a.temperature, top_p=0.9)
                else:
                    output = model.generate(**inputs, **common, do_sample=False)
            raw = tokenizer.decode(
                output[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True,
            )
            code = extract_code(raw)
            expected = puz["test"][0]["output"]
            expected_shape = (len(expected), len(expected[0]))
            run_result = run_code(code, puz["test"][0]["input"])
            mode = classify(code, run_result, expected, expected_shape)
            counts[mode] = counts.get(mode, 0) + 1

            rec = {
                "puzzle": pid, "bucket": 1,
                "prompt_system": system, "prompt_user": user,
                "model_output_raw": raw, "extracted_code": code,
                "test_input": puz["test"][0]["input"],
                "expected_output": expected,
                "got_output": run_result["output"],
                "failure_mode": mode,
            }
            fh.write(json.dumps(rec) + "\n"); fh.flush()

            elapsed = time.time() - t0
            eta = elapsed / i * (len(ids) - i)
            n_pass = counts.get("PASS", 0)
            print(f"[{i:>3}/{len(ids)}] {pid}  {mode:18s}  "
                  f"pass {n_pass}/{i} ({100*n_pass/i:5.1f}%)  "
                  f"elapsed {elapsed:.0f}s  eta {eta:.0f}s")

    # === Report ===
    n = len(ids)
    print(f"\n=== Bucket 1 results ({n} puzzles) ===")
    for mode in ("PASS", "WRONG_OUTPUT", "SHAPE_MISMATCH", "RUNTIME_ERROR",
                 "TIMEOUT", "EMPTY_OR_INVALID", "HARDCODED"):
        c = counts.get(mode, 0)
        bar = "█" * int(50 * c / n) if n else ""
        print(f"  {mode:18s} {c:4d}  ({100*c/n:5.1f}%)  {bar}")
    print()
    print(f"SOLVE RATE: {100*counts.get('PASS', 0)/n:.1f}%")
    print(f"results saved to: {out_path}")


if __name__ == "__main__":
    main()
