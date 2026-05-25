"""Phase-2 eval WITHOUT vLLM — loads Qwen + the LoRA adapter directly via
transformers+peft and runs the same training-matched prompt + functional
validator. Use this when vLLM won't cooperate (flash-attn ABI breaks, MooseFS
download EIO, loader version quirks). Slower (sequential, no paged attention)
but bulletproof: no server, no re-download, no flash-attn.

Run from repo root, pointing HF at the COMPLETE training cache, offline:
  cd /workspace/ARC-AGI2
  HF_HOME=/workspace/hf_cache/huggingface HF_HUB_OFFLINE=1 \
    python "Fine Tune Run 2/run_phase2_eval_local.py" \
      --adapter /root/phase2_code \
      --ids "Fine Tune Run 2/splits/api_eval_ids.txt" --no-test-input

Metric is identical to run_phase2_eval.py: exec the emitted solve(), compare to
ground truth on every train+test pair (grids_eq), pass@2. Code text not compared.
"""
import argparse, json, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phase2_code_dataset import SYSTEM  # noqa
from validate_solver import load_puzzle  # noqa
from run_eval_lora import extract_code, validate  # noqa
from run_phase2_eval import build_user_prompt, resolve_file  # noqa

import torch  # noqa
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa
from peft import PeftModel  # noqa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--adapter", default="/root/phase2_code")
    ap.add_argument("--ids", required=True)
    ap.add_argument("--puzzle-dir", default="Fine Tune Run 2/puzzles_heldout")
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-test-input", action="store_true")
    ap.add_argument("--include-diff", action="store_true")
    args = ap.parse_args()

    print("Loading tokenizer + base model (this is the slow part, ~1-2 min)...")
    tok = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, device_map="cuda",
        attn_implementation="sdpa")
    model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()
    print("Model + adapter loaded.")

    def generate(user):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inp, max_new_tokens=args.max_new_tokens,
                do_sample=args.temperature > 0, temperature=max(args.temperature, 1e-5),
                top_p=0.95, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)

    ids = [x.strip() for x in Path(args.ids).read_text().split() if x.strip()]
    if args.limit:
        ids = ids[:args.limit]
    puzzles, missing, skipped_diff = {}, [], []
    for pid in ids:
        f = resolve_file(pid, args.puzzle_dir)
        if not f:
            missing.append(pid); continue
        pz = load_puzzle(f)
        same = all(len(p["input"]) == len(p["output"]) and len(p["input"][0]) == len(p["output"][0])
                   for p in pz["train"])
        if not same and not args.include_diff:
            skipped_diff.append(pid); continue
        puzzles[pid] = pz
    print(f"{len(puzzles)} puzzles to eval (missing={len(missing)}, skipped_diff={len(skipped_diff)})")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / f"eval_runs/{ts}_phase2local_{Path(args.ids).stem}"
    out.mkdir(parents=True, exist_ok=True)

    results = []
    t0 = time.time()
    n_calls = len(puzzles) * args.attempts
    done = 0
    for pid, pz in puzzles.items():
        user, _ = build_user_prompt(pz, show_test=not args.no_test_input)
        for a in range(args.attempts):
            done += 1
            resp = generate(user)
            code = extract_code(resp)
            rec = {"pid": pid, "attempt": a, "response": resp, "code": code}
            if code is None:
                rec["bucket"] = "no_code"
            else:
                v = validate(code, pz); rec.update(v)
                if v["exec_error"]:        rec["bucket"] = "exec_error"
                elif v["test_pass"] and v["train_pass"]: rec["bucket"] = "correct"
                elif v["train_pass"]:      rec["bucket"] = "wrong_test"
                else:                      rec["bucket"] = "wrong_training"
            (out / f"{pid}__a{a}.json").write_text(json.dumps(rec, indent=2))
            results.append(rec)
            print(f"  [{done:3d}/{n_calls}] {pid} a{a} -> {rec['bucket']}")

    by_pid = {}
    for r in results:
        by_pid.setdefault(r["pid"], []).append(r)
    pass1 = sum(1 for rs in by_pid.values()
                if any(x.get("bucket") == "correct" and x["attempt"] == 0 for x in rs))
    pass2 = sum(1 for rs in by_pid.values() if any(x.get("bucket") == "correct" for x in rs))
    order = ["correct", "wrong_test", "wrong_training", "exec_error", "no_code"]
    best = {}
    for pid, rs in by_pid.items():
        bs = [x.get("bucket") for x in rs]
        best[pid] = min((b for b in bs if b in order), key=order.index, default="no_code")
    hist = {b: sum(1 for v in best.values() if v == b) for b in order}
    summary = {
        "meta": {"adapter": args.adapter, "ids": args.ids, "attempts": args.attempts,
                 "n_puzzles": len(by_pid), "skipped_diff": len(skipped_diff),
                 "elapsed_sec": round(time.time() - t0, 1)},
        "pass_at_1": pass1, "pass_at_2": pass2,
        "pct_pass_at_1": round(100 * pass1 / max(len(by_pid), 1), 2),
        "pct_pass_at_2": round(100 * pass2 / max(len(by_pid), 1), 2),
        "bucket_histogram": hist,
        "solved_puzzle_ids": sorted(pid for pid, b in best.items() if b == "correct"),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"-> {out}/summary.json")


if __name__ == "__main__":
    main()
