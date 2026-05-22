"""Find content-level duplicates in Fine Tune Run 2/puzzles/.

A puzzle is defined by its content, not its filename. Two files are
duplicates if they encode the same puzzle — same multiset of training
pairs and same multiset of test pairs — regardless of the order in
which pairs appear in the JSON.

Pair ordering inside `train` and `test` lists is treated as
insignificant. Everything else (grid values, shapes, palette, test
solution) must match exactly.

Usage:
    python3 analyze_dedupes.py            # analysis only, no changes
    python3 analyze_dedupes.py --dedupe   # remove duplicates, keep one
                                           # per group, merge source tags
                                           # into combined filename
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


PUZZLES_DIR = Path(__file__).resolve().parent.parent / "puzzles"


def canonical_repr(puzzle: dict) -> str:
    """Stable representation independent of pair ordering."""
    train = sorted(
        (pair["input"], pair.get("output", ""))
        for pair in puzzle["train"]
    )
    test = sorted(
        (pair["input"], pair.get("output", ""))
        for pair in puzzle["test"]
    )
    return repr((train, test))


def content_hash(puzzle: dict) -> str:
    return hashlib.sha256(canonical_repr(puzzle).encode()).hexdigest()[:16]


def group_by_content(files: list[Path]) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        puzzle = json.loads(f.read_text())
        groups[content_hash(puzzle)].append(f)
    return groups


def parse_filename(name: str) -> tuple[str, str]:
    """<puzzle_id>_<src>.json -> (puzzle_id, src)."""
    stem = name.removesuffix(".json")
    pid, _, src = stem.partition("_")
    return pid, src


def combined_source_tag(files: list[Path]) -> str:
    """Merge source tags from a duplicate group into a single sorted suffix.
    Example: [00576224_A1E.json, 00576224_A2T.json] -> "A1E+A2T"."""
    srcs = sorted({parse_filename(f.name)[1] for f in files})
    return "+".join(srcs)


def report(groups: dict[str, list[Path]]) -> tuple[int, int, int, int]:
    total = sum(len(v) for v in groups.values())
    unique = len(groups)
    dup_groups = sum(1 for v in groups.values() if len(v) > 1)
    removable = sum(len(v) - 1 for v in groups.values() if len(v) > 1)

    print(f"Total files:                  {total}")
    print(f"Unique puzzles (by content):  {unique}")
    print(f"Duplicate groups (size > 1):  {dup_groups}")
    print(f"Files removable by dedup:     {removable}")
    print(f"Final count after dedup:      {total - removable}")
    return total, unique, dup_groups, removable


def show_samples(groups: dict[str, list[Path]], n: int = 10) -> None:
    print(f"\nFirst {n} duplicate groups (filename only):")
    shown = 0
    for h, names in sorted(groups.items()):
        if len(names) <= 1:
            continue
        print(f"  [{h[:8]}] {sorted(f.name for f in names)}")
        shown += 1
        if shown >= n:
            break


def dedupe(groups: dict[str, list[Path]]) -> None:
    """Keep one file per content group, rename to combined source tag,
    delete the others. Filename pattern: <puzzle_id>_<srcA+srcB+...>.json."""
    kept = 0
    removed = 0
    renamed = 0
    for h, files in groups.items():
        if len(files) == 1:
            kept += 1
            continue
        # All files in this group share the same puzzle_id (since the
        # canonical content matches). Verify and combine src tags.
        pids = {parse_filename(f.name)[0] for f in files}
        merged_tag = combined_source_tag(files)
        # The chosen kept file gets the merged name; the rest are deleted.
        # If pids differ across the group (would be surprising — same
        # content under different ids), we still merge but warn.
        if len(pids) != 1:
            print(f"WARNING group {h[:8]} has multiple ids {pids}; "
                  f"using lexicographically first", file=sys.stderr)
        pid = sorted(pids)[0]
        # Sort files so the kept one is deterministic (first alphabetically)
        files_sorted = sorted(files, key=lambda p: p.name)
        keep = files_sorted[0]
        target = keep.with_name(f"{pid}_{merged_tag}.json")
        # Delete the others first to avoid clashing names
        for f in files_sorted[1:]:
            f.unlink()
            removed += 1
        if target != keep:
            keep.rename(target)
            renamed += 1
        kept += 1
    print(f"\nDedupe done: kept {kept} files, removed {removed}, renamed {renamed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dedupe", action="store_true",
                    help="Apply the dedupe (destructive). Without this flag, "
                         "only report stats.")
    ap.add_argument("--samples", type=int, default=10,
                    help="Number of duplicate groups to show as samples.")
    args = ap.parse_args()

    files = sorted(PUZZLES_DIR.glob("*.json"))
    if not files:
        print(f"No files found in {PUZZLES_DIR}", file=sys.stderr)
        sys.exit(1)

    groups = group_by_content(files)
    report(groups)
    show_samples(groups, args.samples)

    if args.dedupe:
        print("\n--- Applying dedupe ---")
        dedupe(groups)


if __name__ == "__main__":
    main()
