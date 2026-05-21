"""Extract failure data from a bulk_collect run into compact analysis files.

For each puzzle with at least one failure, saves:
- puzzle_id
- per-bucket counts (correct/wrong_training/exec_error/etc.)
- list of wrong attempts with: code, cell_diff (median across train pairs), error

Outputs:
- `<output_dir>/failures.jsonl` — one line per failed (puzzle, run) combo
- `<output_dir>/summary.csv` — per-puzzle counts + median cell_diff
- `<output_dir>/wrong_codes_for_phase_e.jsonl` — formatted as Phase E training records
  (puzzle + wrong_code + feedback -> right_code is missing, we'd need to fill that)

Usage:
    python3 scripts/extract_failures.py <run_dir> <output_dir>

Example:
    python3 scripts/extract_failures.py \\
        bulk_collect_runs/20260521_121542_raw \\
        research/analysis/run1_eval706_failures
"""
import argparse
import csv
import json
import statistics
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="bulk_collect run directory")
    ap.add_argument("output_dir", help="where to save analysis files")
    ap.add_argument("--puzzle-dir", default=None,
                    help="If provided, also embed the original puzzle JSON in failures.jsonl "
                         "for self-contained analysis records.")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Maybe load puzzle map for embedding
    puzzle_map = {}
    if args.puzzle_dir:
        for p in Path(args.puzzle_dir).glob("*.json"):
            try:
                puzzle_map[p.stem] = json.loads(p.read_text())
            except Exception:
                pass
    else:
        for d in ["data/arc1_train", "data/arc1_eval", "data/arc2_train",
                 "data/arc2_eval", "data/augmented_eval", "data/augmented_eval_706"]:
            dp = Path(d)
            if not dp.exists():
                continue
            for p in dp.glob("*.json"):
                puzzle_map.setdefault(p.stem, json.loads(p.read_text()))

    # Aggregate
    failures = []  # list of dicts, one per failed (puzzle, run)
    per_puzzle_stats = {}
    bucket_totals = {}

    for pid_dir in sorted(run_dir.iterdir()):
        if not pid_dir.is_dir():
            continue
        pid = pid_dir.name

        # Skip non-puzzle dirs (e.g., 'run_meta.json' isn't a dir)
        stats = {"correct": 0, "wrong_training": 0, "wrong_test": 0,
                 "exec_error": 0, "no_code": 0, "api_error": 0, "total": 0}

        for run_file in sorted(pid_dir.glob("run_*.json")):
            try:
                rec = json.loads(run_file.read_text())
            except Exception:
                continue
            bucket = rec.get("bucket", "unknown")
            stats[bucket] = stats.get(bucket, 0) + 1
            stats["total"] += 1
            bucket_totals[bucket] = bucket_totals.get(bucket, 0) + 1

            if bucket != "correct":
                # Compute median cell_diff across train pairs
                train_pairs = [p for p in rec.get("pairs", []) if p.get("type") == "train"]
                diffs = [p.get("cell_diff") for p in train_pairs if p.get("cell_diff") is not None]
                median_diff = statistics.median(diffs) if diffs else None

                fail_rec = {
                    "puzzle_id": pid,
                    "run_idx": rec.get("run_idx"),
                    "bucket": bucket,
                    "median_train_diff": median_diff,
                    "exec_error": rec.get("exec_error"),
                    "code": rec.get("code"),
                    "response": rec.get("response"),
                    "pairs": rec.get("pairs"),
                    "usage": rec.get("usage"),
                }
                if pid in puzzle_map:
                    fail_rec["puzzle"] = puzzle_map[pid]
                failures.append(fail_rec)

        per_puzzle_stats[pid] = stats

    # Write failures.jsonl
    failures_path = out_dir / "failures.jsonl"
    with failures_path.open("w") as f:
        for rec in failures:
            f.write(json.dumps(rec) + "\n")

    # Write summary.csv
    csv_path = out_dir / "summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["puzzle_id", "total", "correct", "wrong_training",
                    "wrong_test", "exec_error", "no_code", "api_error",
                    "pass_at_n", "best_train_diff"])
        for pid, stats in sorted(per_puzzle_stats.items()):
            # best_train_diff: among this puzzle's wrong runs, lowest median diff
            pid_failures = [f for f in failures if f["puzzle_id"] == pid
                            and f.get("median_train_diff") is not None]
            best_diff = min((f["median_train_diff"] for f in pid_failures), default=None)
            w.writerow([
                pid, stats["total"], stats["correct"], stats.get("wrong_training", 0),
                stats.get("wrong_test", 0), stats.get("exec_error", 0),
                stats.get("no_code", 0), stats.get("api_error", 0),
                1 if stats["correct"] > 0 else 0,
                best_diff if best_diff is not None else "",
            ])

    # Write phase-e-formatted records (for Run 2 training data, if we want)
    phase_e_path = out_dir / "phase_e_candidates.jsonl"
    with phase_e_path.open("w") as f:
        for fail in failures:
            if not fail.get("code"):
                continue  # need a wrong code for Phase E
            if fail["bucket"] not in ("wrong_training", "exec_error"):
                continue
            if fail["puzzle_id"] not in puzzle_map:
                continue
            f.write(json.dumps({
                "puzzle_id": fail["puzzle_id"],
                "puzzle": puzzle_map[fail["puzzle_id"]],
                "wrong_code": fail["code"],
                "pairs": fail["pairs"],
                "median_train_diff": fail["median_train_diff"],
            }) + "\n")

    # Print summary
    total_puzzles = len(per_puzzle_stats)
    solved = sum(1 for s in per_puzzle_stats.values() if s["correct"] > 0)
    total_failures = len(failures)

    print(f"Extracted from: {run_dir}")
    print(f"  Puzzles: {total_puzzles}")
    print(f"  Solved (pass@N): {solved}")
    print(f"  Failure records: {total_failures}")
    print(f"  Bucket totals across all runs: {bucket_totals}")
    print()
    print(f"Outputs in: {out_dir}")
    print(f"  failures.jsonl              ({failures_path.stat().st_size // 1024} KB)")
    print(f"  summary.csv                 ({csv_path.stat().st_size // 1024} KB)")
    print(f"  phase_e_candidates.jsonl    ({phase_e_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
