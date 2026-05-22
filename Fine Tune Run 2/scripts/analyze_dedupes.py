"""Classify puzzles in Fine Tune Run 2/puzzles/ by content-origin family.

A puzzle is defined by its content, not its filename. Two files encode
the same puzzle if they have the same multiset of training pairs and
the same multiset of test pairs (pair ordering ignored).

For each unique-by-content puzzle, classify which source family it
came from:

    A1-only       only A1T and/or A1E files contain this content
    A2-only       only A2T and/or A2E files contain this content (= new in ARC-2)
    A1-and-A2     both families contain this content (ARC-2 imported it from ARC-1;
                  for accounting we attribute origin to A1 since A1 preceded A2)

The interesting number is A2-only: the count of puzzles that are
genuinely new in ARC-2, not carried over from ARC-1 with shuffled pair
order.

No files are modified. This is read-only analysis.
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


def parse_filename(name: str) -> tuple[str, str]:
    """<puzzle_id>_<src>.json -> (puzzle_id, src)."""
    stem = name.removesuffix(".json")
    pid, _, src = stem.partition("_")
    return pid, src


def classify_origin(sources: set[str]) -> str:
    """A1-only, A2-only, or A1-and-A2."""
    has_a1 = any(s.startswith("A1") for s in sources)
    has_a2 = any(s.startswith("A2") for s in sources)
    if has_a1 and has_a2:
        return "A1-and-A2"
    if has_a1:
        return "A1-only"
    return "A2-only"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=None,
                    help="If given, write per-puzzle manifest JSON here. "
                         "Each row: hash, sources, origin_family, "
                         "representative_filename.")
    args = ap.parse_args()

    files = sorted(PUZZLES_DIR.glob("*.json"))
    if not files:
        print(f"No files in {PUZZLES_DIR}", file=sys.stderr)
        sys.exit(1)

    # Group files by content hash
    groups: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        puzzle = json.loads(f.read_text())
        groups[content_hash(puzzle)].append(f)

    # Counts by origin family
    by_origin: dict[str, int] = defaultdict(int)
    by_origin_singletons: dict[str, int] = defaultdict(int)
    by_origin_multifile: dict[str, int] = defaultdict(int)
    # File-level counts by source tag (raw)
    files_by_src: dict[str, int] = defaultdict(int)
    for f in files:
        files_by_src[parse_filename(f.name)[1]] += 1

    rows = []
    for h, fs in groups.items():
        srcs = {parse_filename(f.name)[1] for f in fs}
        origin = classify_origin(srcs)
        by_origin[origin] += 1
        if len(fs) == 1:
            by_origin_singletons[origin] += 1
        else:
            by_origin_multifile[origin] += 1
        rows.append({
            "hash": h,
            "sources": sorted(srcs),
            "origin_family": origin,
            "files": sorted(f.name for f in fs),
        })

    total_files = sum(files_by_src.values())
    total_unique = sum(by_origin.values())

    print("=" * 60)
    print("File-level counts (by source tag, raw)")
    print("=" * 60)
    for src in sorted(files_by_src):
        print(f"  {src}: {files_by_src[src]}")
    print(f"  TOTAL files: {total_files}")
    print()
    print("=" * 60)
    print("Content-unique puzzles, classified by origin family")
    print("=" * 60)
    print(f"  A1-only        {by_origin['A1-only']:5d}   "
          f"(only ARC-1 has this content)")
    print(f"  A2-only        {by_origin['A2-only']:5d}   "
          f"(genuinely NEW in ARC-2)")
    print(f"  A1-and-A2      {by_origin['A1-and-A2']:5d}   "
          f"(ARC-2 imported from ARC-1, same content)")
    print(f"  TOTAL unique   {total_unique:5d}")
    print()
    print(f"Of the {total_files} files in the corpus, {total_unique} encode")
    print(f"distinct puzzles. The {total_files - total_unique} 'extra' files are")
    print(f"copies that came from A2 importing A1 content with shuffled")
    print(f"pair order — they're attributed to A1 as the origin.")
    print()
    print("=" * 60)
    print(f"What ARC-2 actually added: {by_origin['A2-only']} new puzzles")
    print("=" * 60)
    print(f"  A2T new (training):   "
          f"{sum(1 for r in rows if r['origin_family'] == 'A2-only' and any(s == 'A2T' for s in r['sources']))}")
    print(f"  A2E new (evaluation): "
          f"{sum(1 for r in rows if r['origin_family'] == 'A2-only' and any(s == 'A2E' for s in r['sources']))}")

    if args.manifest:
        args.manifest.write_text(json.dumps(rows, indent=2))
        print(f"\nManifest written to {args.manifest}")


if __name__ == "__main__":
    main()
