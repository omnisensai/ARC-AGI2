#!/usr/bin/env python3
"""Classify each content-unique puzzle by origin family (A1, A2, both).

Reads Fine Tune Run 2/puzzles/*.json (1920 files), groups by canonical
content (train pairs treated as a set; test pairs ordered), and prints
per-source file counts plus content-unique origin breakdown.

Usage:
    python3 classify_origin.py
    python3 classify_origin.py --manifest manifest.json
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


PUZZLES_DIR = Path(__file__).parent / "puzzles"
SOURCES = ("A1T", "A1E", "A2T", "A2E")


def canonical_content(puzzle: dict) -> tuple:
    """Return a hashable canonical form of the puzzle.

    Both train and test pairs are sorted — ARC-2 reshuffles both lists
    when it re-publishes an ARC-1 puzzle, and we want those collapsed.
    """
    train = tuple(sorted(
        (p["input"], p["output"]) for p in puzzle["train"]
    ))
    test = tuple(sorted(
        (p["input"], p["output"]) for p in puzzle["test"]
    ))
    return (train, test)


def parse_filename(path: Path) -> tuple[str, str]:
    """puzzle_id, source_label from <pid>_<src>.json."""
    stem = path.stem
    pid, src = stem.rsplit("_", 1)
    return pid, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=None,
                    help="If given, write per-puzzle origin table here.")
    args = ap.parse_args()

    files = sorted(PUZZLES_DIR.glob("*.json"))

    file_counts = Counter()
    # canonical_content -> {source: [puzzle_ids]}
    by_content = defaultdict(lambda: defaultdict(list))

    for path in files:
        pid, src = parse_filename(path)
        if src not in SOURCES:
            print(f"warn: unknown source in {path.name}", file=sys.stderr)
            continue
        file_counts[src] += 1
        with path.open() as f:
            puzzle = json.load(f)
        key = canonical_content(puzzle)
        by_content[key][src].append(pid)

    # Origin classification per content-unique puzzle.
    a1_only = 0
    a2_only = 0
    both = 0
    a2e_in_a1 = 0  # leakage check
    a2e_total = 0

    rows = []
    for key, srcs in by_content.items():
        present = set(srcs.keys())
        in_a1 = bool(present & {"A1T", "A1E"})
        in_a2 = bool(present & {"A2T", "A2E"})
        if in_a1 and in_a2:
            origin = "A1+A2"
            both += 1
        elif in_a1:
            origin = "A1-only"
            a1_only += 1
        else:
            origin = "A2-only"
            a2_only += 1
        if "A2E" in present:
            a2e_total += 1
            if in_a1:
                a2e_in_a1 += 1
        # pick a representative id (any source's id)
        rep_pid = next(iter(srcs.values()))[0]
        rows.append({
            "rep_pid": rep_pid,
            "origin": origin,
            "sources": {s: ids for s, ids in srcs.items()},
        })

    total_unique = a1_only + a2_only + both

    print("File-level counts:")
    for s in SOURCES:
        print(f"  {s}: {file_counts[s]}")
    print(f"  TOTAL: {sum(file_counts.values())}")
    print()
    print("Content-unique puzzles:")
    print(f"  A1-only      {a1_only}")
    print(f"  A2-only      {a2_only}")
    print(f"  A1-and-A2    {both}")
    print(f"  TOTAL        {total_unique}")
    print()
    print(f"A2E leakage check: {a2e_in_a1}/{a2e_total} A2E puzzles also "
          f"appear in A1 (under canonical pair order).")

    if args.manifest:
        with args.manifest.open("w") as f:
            json.dump(rows, f, indent=2)
        print(f"\nWrote per-puzzle manifest: {args.manifest} "
              f"({len(rows)} entries)")


if __name__ == "__main__":
    main()
