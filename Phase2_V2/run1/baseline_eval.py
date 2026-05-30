"""Baseline eval: run any HuggingFace model (no LoRA) against bucket 1 puzzles.

For paper baselines and comparison. Measures what a base model alone scores
on the same 100 ARC puzzles, so we can quantify what the LoRA contributes.

Usage:
    python3 Phase2_V2/run1/baseline_eval.py \\
        --base-model Qwen/Qwen2.5-7B-Instruct \\
        --limit 100 \\
        --out Phase2_V2/run1/eval/baseline_qwen25_7b.jsonl

Suggested models to compare:
    Qwen/Qwen2.5-7B-Instruct          # our base — measures pure LoRA gain
    Qwen/Qwen2.5-Coder-7B-Instruct    # code-specialized 7B
    meta-llama/Llama-3.1-8B-Instruct  # different family
    Qwen/Qwen2.5-14B-Instruct         # larger Qwen (fits 80GB H100)
    deepseek-ai/deepseek-coder-7b-instruct-v1.5

Notes:
- Base models benefit from sampling (T=0.5) more than fine-tunes
- They don't know substrate-curriculum — give them general "write Python" framing
"""
import argparse, ast, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
P2 = REPO / "Phase2_V2"
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import audit as _ast_audit


# Different SYSTEM for baseline models — they don't know our substrate jargon.
# Use a generic but informative ARC framing.
BASELINE_SYSTEM = (
    "You are solving ARC-AGI puzzles. For each puzzle you're given several "
    "INPUT/OUTPUT training pairs that all follow the SAME transformation rule. "
    "Your task: write a Python function `def solve(input_grid)` that applies "
    "that rule to any input.\n\n"
    "input_grid is a list of lists of integers 0-9 (a 2D grid of colors). "
    "Return a list of lists of integers (the transformed grid).\n\n"
    "Infer the rule from the training pairs. Do not hardcode any specific grid "
    "or compare against a known input. Return Python code only."
)


def load_puzzle(pid):
    p = P2 / "canonical" / "ground_truth_puzzles" / f"{pid}.json"
    return json.loads(p.read_text())


def grid_to_str(g):
    return "\n".join("".join(str(c) for c in row) for row in g)


def build_user_prompt(puzzle):
    """Build a clean USER prompt with INPUT/OUTPUT pairs (no T)."""
    blocks = []
    for i, p in enumerate(puzzle["train"], 1):
        blocks.append(f"PAIR {i}:\nINPUT:\n{grid_to_str(p['input'])}\n"
                      f"OUTPUT:\n{grid_to_str(p['output'])}")
    return "\n\n".join(blocks) + "\n\nWrite def solve(input_grid)."


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
    return "PASS" if out == expected else "WRONG_OUTPUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True,
                    help="HF model id, e.g. Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--temperature", type=float, default=0.5,
                    help="0.0 = greedy, 0.5 = mild sampling (default — better for base models)")
    ap.add_argument("--strict-prompt", action="store_true",
                    help="Use the EXACT substrate prompt the LoRA was trained on "
                         "(INPUT + T instead of INPUT + OUTPUT). For apples-to-apples "
                         "fairness comparison. Baseline won't understand T jargon, "
                         "but it's the same prompt the LoRA gets.")
    ap.add_argument("--out", default=None,
                    help="output JSONL. Default: baseline_<modelname>.jsonl")
    args = ap.parse_args()

    # If strict-prompt, import the substrate SYSTEM + renderer the LoRA was trained on
    if args.strict_prompt:
        sys.path.insert(0, str(P2 / "micro"))
        from build_micro_sft import SYSTEM as STRICT_SYSTEM, render_pairs as strict_render
        global BASELINE_SYSTEM, build_user_prompt
        BASELINE_SYSTEM = STRICT_SYSTEM
        def build_user_prompt(puzzle):
            return strict_render(puzzle["train"]) + "\n\nWrite def solve(input_grid)."

    out_path = Path(args.out or P2 / "run1/eval" /
                    f"baseline_{args.base_model.split('/')[-1].lower()}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ids = (P2 / "run1/splits/bucket1_trained_sample.txt").read_text().split()[:args.limit]
    print(f"loading {len(ids)} puzzles ...")
    puzzles = {pid: load_puzzle(pid) for pid in ids}

    print(f"loading {args.base_model} ...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    try:
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_flash_sdp(False)
    except Exception:
        pass

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="eager",
    )
    model.eval()
    print("ready.")

    counts = {}
    t0 = time.time()
    with out_path.open("w") as fh:
        for i, pid in enumerate(ids, 1):
            puz = puzzles[pid]
            user = build_user_prompt(puz)
            prompt = tokenizer.apply_chat_template(
                [{"role": "system", "content": BASELINE_SYSTEM},
                 {"role": "user", "content": user}],
                tokenize=False, add_generation_prompt=True,
            )
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                if args.temperature > 0:
                    output = model.generate(
                        **inputs, max_new_tokens=args.max_new_tokens,
                        do_sample=True, temperature=args.temperature, top_p=0.9,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                else:
                    output = model.generate(
                        **inputs, max_new_tokens=args.max_new_tokens,
                        do_sample=False, pad_token_id=tokenizer.eos_token_id,
                    )
            raw = tokenizer.decode(output[0][inputs.input_ids.shape[1]:],
                                   skip_special_tokens=True)
            code = extract_code(raw)
            expected = puz["test"][0]["output"]
            expected_shape = (len(expected), len(expected[0]))
            run_result = run_code(code, puz["test"][0]["input"])
            mode = classify(code, run_result, expected, expected_shape)
            counts[mode] = counts.get(mode, 0) + 1

            rec = {
                "puzzle": pid, "model": args.base_model,
                "prompt_system": BASELINE_SYSTEM, "prompt_user": user,
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

    print(f"\n=== Baseline {args.base_model} ({len(ids)} puzzles) ===")
    for mode in ("PASS", "WRONG_OUTPUT", "SHAPE_MISMATCH", "RUNTIME_ERROR",
                 "TIMEOUT", "EMPTY_OR_INVALID", "HARDCODED"):
        c = counts.get(mode, 0)
        bar = "█" * int(50 * c / len(ids))
        print(f"  {mode:18s} {c:4d}  ({100*c/len(ids):5.1f}%)  {bar}")
    print()
    print(f"SOLVE RATE: {100*counts.get('PASS', 0)/len(ids):.1f}%")
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
