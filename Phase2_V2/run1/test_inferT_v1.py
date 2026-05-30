"""V1 LoRA self-consistency test: ask for infer_T only, verify on SEEN train pairs.

Different from solve eval — we don't ask the model to generalize to the test
input. We give it the train pairs (INPUT + T), ask it to write infer_T, and
then run infer_T on each train pair's input. If infer_T(train_input) reproduces
the demonstrated T, the LoRA actually encoded the rule. If not, the model is
emitting plausible-looking code without truly extracting the transformation.

This separates two failure modes:
  A. Rule extraction broken (can't even self-consistent on seen pairs)
  B. Rule extraction OK, generalization-to-test broken

Usage:
    python3 Phase2_V2/run1/test_inferT_v1.py \\
        --lora v1_lora/phase2_code \\
        --limit 10
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
P2 = REPO / "Phase2_V2"
sys.path.insert(0, str(P2 / "micro"))

from build_micro_sft import SYSTEM, render_pairs


def load_puzzle(pid):
    p = P2 / "canonical" / "ground_truth_puzzles" / f"{pid}.json"
    return json.loads(p.read_text())


def expected_T(inp, out):
    """Per-cell change map as a dict {(r,c): new_value}."""
    T = {}
    for r in range(len(inp)):
        for c in range(len(inp[0])):
            if inp[r][c] != out[r][c]:
                T[(r, c)] = out[r][c]
    return T


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


def run_inferT(code, test_input, timeout=3.0):
    """Run extracted code, call infer_T(input), return the dict (or error)."""
    runner = (
        f"import sys, json\n"
        f"code = {code!r}\n"
        f"ns = {{}}\n"
        f"try:\n"
        f"    exec(code, ns)\n"
        f"    fn = ns.get('infer_T')\n"
        f"    if fn is None: raise RuntimeError('no infer_T function')\n"
        f"    inp = json.loads(sys.stdin.read())\n"
        f"    T = fn(inp)\n"
        f"    if not isinstance(T, dict):\n"
        f"        raise RuntimeError(f'infer_T returned {{type(T).__name__}}, expected dict')\n"
        f"    items = [[list(k) if isinstance(k, tuple) else k, v] for k, v in T.items()]\n"
        f"    print('OK'); print(json.dumps(items))\n"
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
            items = json.loads(lines[1])
            T = {tuple(k) if isinstance(k, list) else k: v for k, v in items}
            return {"ok": True, "T": T, "error": None}
        return {"ok": False, "T": None,
                "error": lines[1] if len(lines) > 1 else result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "T": None, "error": "TIMEOUT"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True)
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.5)
    ap.add_argument("--out", default=str(P2 / "run1/eval/v1_inferT_test.jsonl"))
    a = ap.parse_args()

    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ids = (P2 / "run1/splits/bucket1_trained_sample.txt").read_text().split()[:a.limit]
    print(f"loading {len(ids)} puzzles ...")
    puzzles = {pid: load_puzzle(pid) for pid in ids}

    print(f"loading base + LoRA ...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    try:
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_flash_sdp(False)
    except Exception:
        pass

    tokenizer = AutoTokenizer.from_pretrained(a.base_model)
    base = AutoModelForCausalLM.from_pretrained(
        a.base_model, torch_dtype=torch.bfloat16,
        device_map="cuda", attn_implementation="eager",
    )
    model = PeftModel.from_pretrained(base, a.lora)
    model.eval()
    print("ready.")

    t0 = time.time()
    overall_pairs = 0
    overall_correct = 0
    puzzles_all_correct = 0
    with out_path.open("w") as fh:
        for i, pid in enumerate(ids, 1):
            puz = puzzles[pid]
            # Build prompt — same SYSTEM and pair format, but ask for infer_T only
            user = render_pairs(puz["train"]) + "\n\nWrite def infer_T(input_grid)."
            prompt = tokenizer.apply_chat_template(
                [{"role": "system", "content": SYSTEM},
                 {"role": "user", "content": user}],
                tokenize=False, add_generation_prompt=True,
            )
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                if a.temperature > 0:
                    out = model.generate(
                        **inputs, max_new_tokens=a.max_new_tokens,
                        do_sample=True, temperature=a.temperature, top_p=0.9,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                else:
                    out = model.generate(
                        **inputs, max_new_tokens=a.max_new_tokens,
                        do_sample=False, pad_token_id=tokenizer.eos_token_id,
                    )
            raw = tokenizer.decode(out[0][inputs.input_ids.shape[1]:],
                                   skip_special_tokens=True)
            code = extract_code(raw)

            # Run infer_T on EACH train pair's input, compare to expected T
            pair_results = []
            for pi, pair in enumerate(puz["train"]):
                exp = expected_T(pair["input"], pair["output"])
                r = run_inferT(code, pair["input"])
                if r["ok"]:
                    got = r["T"]
                    match = (got == exp)
                else:
                    got = None
                    match = False
                pair_results.append({
                    "pair_index": pi,
                    "ok": r["ok"], "error": r["error"],
                    "expected_count": len(exp),
                    "got_count": len(got) if got is not None else None,
                    "exact_match": match,
                })

            n_pairs = len(pair_results)
            n_correct = sum(1 for r in pair_results if r["exact_match"])
            overall_pairs += n_pairs
            overall_correct += n_correct
            all_correct = (n_correct == n_pairs)
            if all_correct: puzzles_all_correct += 1

            rec = {
                "puzzle": pid,
                "prompt_system": SYSTEM, "prompt_user": user,
                "model_output_raw": raw, "extracted_code": code,
                "n_train_pairs": n_pairs, "n_correct": n_correct,
                "all_correct": all_correct,
                "pair_results": pair_results,
            }
            fh.write(json.dumps(rec) + "\n"); fh.flush()

            elapsed = time.time() - t0
            status = "ALL" if all_correct else f"{n_correct}/{n_pairs}"
            print(f"[{i:>3}/{len(ids)}] {pid}  infer_T correct on train pairs: "
                  f"{status:>6s}   elapsed {elapsed:.0f}s")

    n = len(ids)
    print(f"\n=== V1 infer_T self-consistency ({n} puzzles) ===")
    print(f"  puzzles where infer_T worked on ALL train pairs: "
          f"{puzzles_all_correct}/{n} ({100*puzzles_all_correct/n:.1f}%)")
    print(f"  pair-level correctness: "
          f"{overall_correct}/{overall_pairs} ({100*overall_correct/overall_pairs:.1f}%)")
    print(f"  results: {out_path}")


if __name__ == "__main__":
    main()
