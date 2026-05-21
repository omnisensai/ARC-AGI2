"""Analyze wrong_training failures from a bulk_collect run.

For each puzzle that had >=1 wrong_training in its 10 attempts, prints:
- puzzle_id
- correct/wrong split (e.g. 3 correct / 7 wrong)
- median cell_diff across wrong attempts (how "close" the wrong code was)
- one representative wrong code snippet (the one with lowest cell_diff)

Also exports a CSV of all wrong_training records for offline analysis.

Usage:
    python3 scripts/analyze_failures.py <run_dir>
    python3 scripts/analyze_failures.py bulk_collect_runs/20260521_121542_raw

Example output:
    Run: 20260521_121542_raw
    Total puzzles: 706
    Puzzles with all 10 wrong: 105
    Puzzles partially wrong (1-9 wrong of 10): 432
    Puzzles all correct (0 wrong of 10): 169

    Worst 10 puzzles (highest median cell_diff among wrongs):
      ...
"""
import argparse
import csv
import json
import statistics
from pathlib import Path
from collections import defaultdict


def analyze(run_dir: Path, csv_out: Path = None, top_n: int = 20):
    by_puzzle = defaultdict(list)  # pid -> [run_record]
    for pid_dir in run_dir.iterdir():
        if not pid_dir.is_dir():
            continue
        for run_file in pid_dir.glob("run_*.json"):
            try:
                rec = json.loads(run_file.read_text())
                rec["_file"] = str(run_file)
                by_puzzle[pid_dir.name].append(rec)
            except Exception:
                continue

    total = len(by_puzzle)
    all_wrong = 0
    partial = 0
    all_correct = 0
    per_puzzle_stats = []

    for pid, runs in by_puzzle.items():
        buckets = [r.get("bucket") for r in runs]
        n_correct = buckets.count("correct")
        n_wrong = buckets.count("wrong_training")
        n_exec = buckets.count("exec_error")
        n_runs = len(runs)
        if n_correct == n_runs:
            all_correct += 1
            continue
        if n_correct == 0 and n_wrong + n_exec == n_runs:
            all_wrong += 1
        else:
            partial += 1

        # Compute median cell_diff across wrong_training runs
        diffs = []
        for r in runs:
            if r.get("bucket") != "wrong_training":
                continue
            # Take median cell_diff across this run's train pairs
            pair_diffs = [p.get("cell_diff") for p in r.get("pairs", [])
                          if p.get("type") == "train" and p.get("cell_diff") is not None]
            if pair_diffs:
                diffs.append(statistics.median(pair_diffs))

        if diffs:
            median_diff = statistics.median(diffs)
        else:
            median_diff = None

        # Pick a representative wrong run: lowest cell_diff among wrongs
        rep = None
        rep_diff = None
        for r in runs:
            if r.get("bucket") != "wrong_training":
                continue
            pair_diffs = [p.get("cell_diff") for p in r.get("pairs", [])
                          if p.get("type") == "train" and p.get("cell_diff") is not None]
            d = statistics.median(pair_diffs) if pair_diffs else None
            if d is not None and (rep_diff is None or d < rep_diff):
                rep_diff = d
                rep = r

        per_puzzle_stats.append({
            "pid": pid,
            "n_correct": n_correct,
            "n_wrong": n_wrong,
            "n_exec": n_exec,
            "median_diff": median_diff,
            "rep_code": rep.get("code", "")[:300] if rep else "",
        })

    print(f"Run: {run_dir.name}")
    print(f"Total puzzles: {total}")
    print(f"  All correct  (0 wrong): {all_correct}")
    print(f"  Partial      (1-9 wrong): {partial}")
    print(f"  All wrong    (10/10):  {all_wrong}")
    print()
    print(f"Top {top_n} hardest puzzles (highest median cell_diff among wrongs):")
    sorted_stats = sorted(
        [s for s in per_puzzle_stats if s["median_diff"] is not None],
        key=lambda s: -s["median_diff"],
    )
    for s in sorted_stats[:top_n]:
        print(f"  {s['pid']}  correct={s['n_correct']}  wrong={s['n_wrong']}  "
              f"median_diff={s['median_diff']:.1f}")

    print()
    print(f"Closest 'almost solved' puzzles (lowest median cell_diff among wrongs):")
    for s in sorted_stats[-top_n:]:
        print(f"  {s['pid']}  correct={s['n_correct']}  wrong={s['n_wrong']}  "
              f"median_diff={s['median_diff']:.1f}")

    if csv_out:
        with csv_out.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["pid", "n_correct", "n_wrong", "n_exec", "median_diff", "rep_code_snippet"])
            for s in per_puzzle_stats:
                w.writerow([s["pid"], s["n_correct"], s["n_wrong"], s["n_exec"],
                            s["median_diff"], s["rep_code"].replace("\n", "\\n")])
        print(f"\nFull CSV written to: {csv_out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="bulk_collect run directory")
    ap.add_argument("--csv", default=None, help="optional CSV output path")
    ap.add_argument("--top-n", type=int, default=20)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    if not rd.exists():
        rd2 = Path("bulk_collect_runs") / args.run_dir
        if rd2.exists():
            rd = rd2
    csv_out = Path(args.csv) if args.csv else None
    analyze(rd, csv_out, args.top_n)


if __name__ == "__main__":
    main()
