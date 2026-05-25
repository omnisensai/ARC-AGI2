"""Phase-2 code-solver eval — prompts the model EXACTLY like training, then runs
the generated code against ground truth (functional scoring, pass@2).

Why this exists and not run_eval_lora.py: that script is the Run-1 harness; its
prompt (system tag "D", raw Input/Output, no T) does NOT match Phase-2 training,
so it would query the adapter out-of-distribution and under-report. This harness
imports the generator's own SYSTEM / grid_str / t_text / demos_block, so the
prompt is byte-identical to what the model trained on. The code executor and
ground-truth comparison are reused from run_eval_lora unchanged.

The metric is functional: we exec the emitted solve() and compare its output to
ground truth on every train + test pair (grids_eq). Code text is never compared.

Usage (vLLM must be serving the adapter as model 'arc' on :8000):
  # clean official-eval dev probe (the 30)
  python "Fine Tune Run 2/run_phase2_eval.py" --ids "Fine Tune Run 2/splits/phase2_dev_eval_ids.txt"
  # train-pool sanity set (the 50)
  python "Fine Tune Run 2/run_phase2_eval.py" --ids "Fine Tune Run 2/splits/api_eval_ids.txt"
  # SACRED — run once, at the very end
  python "Fine Tune Run 2/run_phase2_eval.py" --ids "Fine Tune Run 2/splits/frozen_final_eval_ids.txt" --puzzle-dir "Fine Tune Run 2/puzzles_frozen"
"""
import argparse, glob, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Single source of truth: the exact prompt pieces the dataset was built with.
from build_phase2_code_dataset import SYSTEM, grid_str, demos_block  # noqa
from validate_solver import load_puzzle  # noqa
# Reuse the executor + ground-truth comparator unchanged.
from run_eval_lora import extract_code, validate, call_vllm  # noqa


def build_user_prompt(pz, show_test=True):
    """Mirror make_record() in the generator: all train pairs as evidence
    (compact INPUT+T for same-size, INPUT+OUTPUT+T for diff-size), then a bare
    TEST INPUT (no T — we must not leak the answer), then the trailing cue."""
    pairs = pz["train"]
    same = all(len(p["input"]) == len(p["output"]) and len(p["input"][0]) == len(p["output"][0])
               for p in pairs)
    user = demos_block(pairs, list(range(len(pairs))), compact=same)
    if show_test and pz["test"]:
        user += f"\n\nTEST INPUT:\n{grid_str(pz['test'][0]['input'])}"
    user += "\n\nWrite def solve(input_grid):"
    return user, same


def resolve_file(pid, puzzle_dir):
    # Prefer ARC-AGI-2 eval, then ARC-2 train, then ARC-1 variants.
    for suf in ("_A2E", "_A2T", "_A1E", "_A1T", ""):
        f = Path(puzzle_dir) / f"{pid}{suf}.json"
        if f.exists():
            return str(f)
    hits = glob.glob(f"{puzzle_dir}/{pid}*.json")
    return hits[0] if hits else None


def run_one(args, pid, puzzle, attempt):
    user, _ = build_user_prompt(puzzle, show_test=not args.no_test_input)
    try:
        resp = call_vllm(args.api_base, args.model, SYSTEM, user, args.temperature, args.max_tokens)
    except Exception as e:
        return {"pid": pid, "attempt": attempt, "bucket": "api_error", "error": str(e)}
    code = extract_code(resp)
    rec = {"pid": pid, "attempt": attempt, "response": resp, "code": code}
    if code is None:
        rec["bucket"] = "no_code"; return rec
    v = validate(code, puzzle)
    rec.update(v)
    if v["exec_error"]:        rec["bucket"] = "exec_error"
    elif v["test_pass"] and v["train_pass"]: rec["bucket"] = "correct"
    elif v["train_pass"]:      rec["bucket"] = "wrong_test"
    else:                      rec["bucket"] = "wrong_training"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="arc", help="'arc' = LoRA adapter; or a base model id")
    ap.add_argument("--ids", required=True, help="txt file of puzzle ids, one per line")
    ap.add_argument("--puzzle-dir", default="Fine Tune Run 2/puzzles_heldout")
    ap.add_argument("--attempts", type=int, default=2, help="ARC-AGI-2 scores pass@2")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--no-test-input", action="store_true", help="omit TEST INPUT (all_pairs shape)")
    ap.add_argument("--include-diff", action="store_true",
                    help="also eval diff-size puzzles (this adapter trained same-only; off by default)")
    args = ap.parse_args()

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
    if missing:
        print(f"MISSING {len(missing)} (first 5: {missing[:5]}) — check --puzzle-dir")
    if skipped_diff:
        print(f"SKIPPED {len(skipped_diff)} diff-size puzzles (adapter is same-only; use --include-diff to force)")
    if not puzzles:
        print("No puzzles to eval."); sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / f"eval_runs/{ts}_phase2_{Path(args.ids).stem}_{args.model.replace('/', '_')}"
    out.mkdir(parents=True, exist_ok=True)

    tasks = [(pid, puzzles[pid], a) for pid in puzzles for a in range(args.attempts)]
    print(f"{len(puzzles)} puzzles x {args.attempts} attempts = {len(tasks)} calls, model={args.model}")

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, args, pid, p, a): (pid, a) for pid, p, a in tasks}
        done = 0
        for fut in as_completed(futs):
            pid, a = futs[fut]; done += 1
            r = fut.result()
            (out / f"{pid}__a{a}.json").write_text(json.dumps(r, indent=2))
            results.append(r)
            print(f"  [{done:3d}/{len(tasks)}] {pid} a{a} -> {r.get('bucket')}")

    by_pid = {}
    for r in results:
        by_pid.setdefault(r["pid"], []).append(r)
    pass1 = sum(1 for rs in by_pid.values()
                if any(x.get("bucket") == "correct" and x.get("attempt") == 0 for x in rs))
    pass2 = sum(1 for rs in by_pid.values() if any(x.get("bucket") == "correct" for x in rs))
    # bucket histogram (best bucket per puzzle, by severity)
    order = ["correct", "wrong_test", "wrong_training", "exec_error", "no_code", "api_error"]
    best = {}
    for pid, rs in by_pid.items():
        bs = [x.get("bucket") for x in rs]
        best[pid] = min((b for b in bs if b in order), key=order.index, default="api_error")
    hist = {b: sum(1 for v in best.values() if v == b) for b in order}
    summary = {
        "meta": {"model": args.model, "ids": args.ids, "attempts": args.attempts,
                 "temperature": args.temperature, "n_puzzles": len(by_pid),
                 "skipped_diff": len(skipped_diff), "missing": len(missing),
                 "elapsed_sec": round(time.time() - t0, 1)},
        "pass_at_1": pass1, "pass_at_2": pass2,
        "pct_pass_at_1": round(100 * pass1 / len(by_pid), 2),
        "pct_pass_at_2": round(100 * pass2 / len(by_pid), 2),
        "bucket_histogram": hist,
        "solved_puzzle_ids": sorted(pid for pid, b in best.items() if b == "correct"),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"-> {out}/summary.json")


if __name__ == "__main__":
    main()
