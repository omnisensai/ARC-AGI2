"""Pick N puzzles from the pool for a new collection batch.

Reads STATUS.csv (run update_status.py first) and filters by the predicate
you choose. Writes a splits/<name>.json that bulk_collect.py and the agent
prompt builder can consume.

Usage:
    # Default: 50 unsolved same-size training puzzles, random seed 1
    python3 pick_batch.py --out splits/batch_002.json

    # Pick puzzles where Qwen ran but we don't have a Claude right code yet
    python3 pick_batch.py --filter needs-right --n 20 --out splits/needs_right.json

    # Pick puzzles where Claude solved but Qwen hasn't run yet
    python3 pick_batch.py --filter needs-wrong --n 20 --out splits/needs_wrong.json

    # Restrict to one source dataset
    python3 pick_batch.py --source arc2_train --n 50 --out splits/arc2_only.json

    # Show candidates without writing (dry-run)
    python3 pick_batch.py --filter unsolved --n 10 --dry-run

Filters:
    unsolved       n_right=0 AND n_wrong=0 (default) - fresh untouched puzzles
    needs-wrong    n_right>0 AND n_wrong=0 - has right code, run Qwen on these
    needs-right    n_wrong>0 AND n_right=0 - has Qwen wrong codes, run agents
    needs-both     n_right=0 OR n_wrong=0 - missing at least one half
    all            no filter beyond same-size and not-locked
"""
import argparse
import csv
import json
import random
from pathlib import Path


def parse_status_csv(path: Path):
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            r["n_right"] = int(r["n_right"])
            r["n_wrong"] = int(r["n_wrong"])
            r["phase3_pairs"] = int(r["phase3_pairs"])
            rows.append(r)
    return rows


def apply_filter(rows, filter_name: str):
    f = filter_name
    if f == "unsolved":
        return [r for r in rows if r["n_right"] == 0 and r["n_wrong"] == 0]
    if f == "needs-wrong":
        return [r for r in rows if r["n_right"] > 0 and r["n_wrong"] == 0]
    if f == "needs-right":
        return [r for r in rows if r["n_wrong"] > 0 and r["n_right"] == 0]
    if f == "needs-both":
        return [r for r in rows if r["n_right"] == 0 or r["n_wrong"] == 0]
    if f == "all":
        return rows
    raise SystemExit(f"unknown filter: {filter_name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", default="STATUS.csv")
    ap.add_argument("--out", required=False, help="output split JSON path (e.g. splits/batch_002.json)")
    ap.add_argument("--n", type=int, default=50, help="how many puzzles to pick")
    ap.add_argument("--filter", default="unsolved",
                    choices=["unsolved", "needs-wrong", "needs-right", "needs-both", "all"])
    ap.add_argument("--source", default=None, choices=[None, "arc1_train", "arc1_eval", "arc2_train"],
                    help="restrict to one source dataset (arc2_eval is locked, never picked)")
    ap.add_argument("--same-size-only", action="store_true", default=True,
                    help="(default) only pick puzzles whose train+test pairs all have input.shape == output.shape")
    ap.add_argument("--include-diff-size", action="store_true",
                    help="allow different-size puzzles too")
    ap.add_argument("--seed", type=int, default=1, help="random seed for reproducibility")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = parse_status_csv(Path(args.status))

    # Hard exclusions
    rows = [r for r in rows if not r["locked"]]                       # never pick arc2_eval
    if args.source:
        rows = [r for r in rows if r["source"] == args.source]
    if not args.include_diff_size:
        rows = [r for r in rows if r["same_size"] == "y"]

    # Filter
    candidates = apply_filter(rows, args.filter)

    print(f"Candidate pool after filters: {len(candidates)} puzzles "
          f"(filter={args.filter}, source={args.source or 'any'}, "
          f"same-size={'no' if args.include_diff_size else 'yes'})")

    if len(candidates) < args.n:
        print(f"WARNING: pool has {len(candidates)} but you asked for {args.n}. Picking all.")
        args.n = len(candidates)

    rng = random.Random(args.seed)
    picked = rng.sample(candidates, args.n)
    picked_ids = sorted(r["puzzle_id"] for r in picked)

    print(f"\nPicked {len(picked_ids)} puzzles (seed={args.seed}):")
    by_source = {}
    for r in picked:
        by_source.setdefault(r["source"], []).append(r["puzzle_id"])
    for src, ids in sorted(by_source.items()):
        print(f"  {src}: {len(ids)}")
    print(f"\n  first 10 IDs: {picked_ids[:10]}")

    if args.dry_run:
        print("\n(--dry-run: nothing written)")
        return

    if not args.out:
        raise SystemExit("must pass --out <path> or --dry-run")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "description": f"Batch picked by pick_batch.py (filter={args.filter}, source={args.source or 'any'}, seed={args.seed})",
        "filter": args.filter,
        "seed": args.seed,
        "puzzle_ids": picked_ids,
    }, indent=2))
    print(f"\nWrote {out_path}")
    print(f"\nNext: python3 bulk_collect.py --splits {out_path}")


if __name__ == "__main__":
    main()
