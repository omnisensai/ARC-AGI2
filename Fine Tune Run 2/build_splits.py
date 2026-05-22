#!/usr/bin/env python3
"""Deterministic split + physical isolation of the frozen final-eval set.

Reads:
  Fine Tune Run 2/puzzles/*.json                  (1920 raw files)
  Fine Tune Run 2/phase1a_config.yaml             (seed, split counts)

Writes:
  Fine Tune Run 2/splits/phase1_splits.json       (source-of-truth manifest)
  Fine Tune Run 2/splits/frozen_final_eval_ids.txt(34 pids, one per line)

Then moves every puzzle file matching the 34 frozen ids out of
puzzles/ into puzzles_frozen/. After this script runs, puzzles/ no
longer contains any frozen-eval puzzle — the dataset generator
physically cannot read them.

Idempotency: if puzzles_frozen/ already contains files, the script
refuses to re-split unless --force-rebalance is passed. This is to
prevent accidentally rolling a fresh frozen set after the original
has already been used for an eval (which would invalidate the eval).

Usage:
    python3 "Fine Tune Run 2/build_splits.py"
    python3 "Fine Tune Run 2/build_splits.py" --force-rebalance
    python3 "Fine Tune Run 2/build_splits.py" --dry-run
"""
import argparse
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUZZLES_DIR = ROOT / "puzzles"
FROZEN_DIR = ROOT / "puzzles_frozen"
SPLITS_DIR = ROOT / "splits"
SPLITS_JSON = SPLITS_DIR / "phase1_splits.json"
FROZEN_IDS_TXT = SPLITS_DIR / "frozen_final_eval_ids.txt"

SOURCES = ("A1T", "A1E", "A2T", "A2E")

# Locked in phase1a_config.yaml / phase1b_config.yaml. Hard-coded here
# rather than parsed from YAML so this script has no extra deps and
# the values stay diffable in version control alongside the script.
SEED = 42
COUNT_A2E_FINAL_HARD = 34
COUNT_A2E_DEV_HARD = 30
COUNT_A2E_TRAIN_HARD = 50


# --- helpers ---------------------------------------------------------------

def parse_filename(path: Path) -> tuple[str, str]:
    pid, src = path.stem.rsplit("_", 1)
    return pid, src


def canonical_content(puzzle: dict) -> tuple:
    """Train + test pairs as unordered sets (ARC-2 reshuffles both)."""
    train = tuple(sorted((p["input"], p["output"]) for p in puzzle["train"]))
    test = tuple(sorted((p["input"], p["output"]) for p in puzzle["test"]))
    return (train, test)


def first_pair(puzzle: dict) -> dict:
    return puzzle["train"][0]


def grid_dims(grid_str: str) -> tuple[int, int]:
    rows = grid_str.split("\n")
    return len(rows), len(rows[0])


def size_bucket(puzzle: dict) -> str:
    """small / medium / large by the first train pair's input shape."""
    h, w = grid_dims(first_pair(puzzle)["input"])
    if h <= 6 and w <= 6:
        return "small"
    if h <= 15 and w <= 15:
        return "medium"
    return "large"


def pair_shape_mix(puzzle: dict) -> str:
    """all_S / all_D / mixed across train+test pairs."""
    same = []
    for p in puzzle["train"] + puzzle["test"]:
        ih, iw = grid_dims(p["input"])
        oh, ow = grid_dims(p["output"])
        same.append((ih, iw) == (oh, ow))
    if all(same):
        return "all_S"
    if not any(same):
        return "all_D"
    return "mixed"


def n_test_bucket(puzzle: dict) -> str:
    return "one" if len(puzzle["test"]) == 1 else "many"


def stratum_key(puzzle: dict) -> tuple:
    return (size_bucket(puzzle), pair_shape_mix(puzzle), n_test_bucket(puzzle))


# --- main logic ------------------------------------------------------------

def load_clusters():
    """Group all puzzle files into content-unique clusters.

    Returns a list of cluster dicts:
        {"pids": set of pids, "sources": set of source labels,
         "files": list of file paths, "stratum": (...), "puzzle": dict}
    where "puzzle" is one canonical loaded JSON (any file in the cluster
    suffices — they have identical content by construction).
    """
    by_content = defaultdict(list)
    for path in sorted(PUZZLES_DIR.glob("*.json")):
        pid, src = parse_filename(path)
        if src not in SOURCES:
            continue
        with path.open() as f:
            data = json.load(f)
        by_content[canonical_content(data)].append({
            "path": path, "pid": pid, "src": src, "data": data,
        })

    clusters = []
    for content, files in by_content.items():
        pids = {f["pid"] for f in files}
        sources = {f["src"] for f in files}
        rep_pid = min(pids)  # deterministic representative
        clusters.append({
            "rep_pid": rep_pid,
            "pids": sorted(pids),
            "sources": sorted(sources),
            "files": sorted(str(f["path"].name) for f in files),
            "stratum": stratum_key(files[0]["data"]),
            "n_train": len(files[0]["data"]["train"]),
            "n_test": len(files[0]["data"]["test"]),
        })

    clusters.sort(key=lambda c: c["rep_pid"])
    return clusters


def categorize(clusters):
    """Split clusters into (a2e_leakers, a2e_only, non_a2e)."""
    a2e_leakers = []
    a2e_only = []
    non_a2e = []
    for c in clusters:
        srcs = set(c["sources"])
        if "A2E" in srcs and srcs & {"A1T", "A1E"}:
            a2e_leakers.append(c)
        elif "A2E" in srcs:
            a2e_only.append(c)
        else:
            non_a2e.append(c)
    return a2e_leakers, a2e_only, non_a2e


def stratified_assign(items, targets, seed):
    """Partition items into named buckets honoring stratum balance.

    items: list of cluster dicts (each with a "stratum" key).
    targets: dict bucket_name -> exact count. Must sum to len(items).

    Returns dict bucket_name -> list of clusters.
    """
    total_in = len(items)
    total_target = sum(targets.values())
    if total_in != total_target:
        raise ValueError(
            f"stratified_assign: {total_in} items vs {total_target} target slots"
        )

    rng = random.Random(seed)
    strata = defaultdict(list)
    for it in items:
        strata[it["stratum"]].append(it)
    for s in strata:
        strata[s].sort(key=lambda c: c["rep_pid"])
        rng.shuffle(strata[s])

    bucket_names = list(targets.keys())
    assignments = {b: [] for b in bucket_names}

    # Phase 1: per-stratum proportional with largest-remainder rounding.
    leftovers = {b: 0 for b in bucket_names}
    for s in sorted(strata.keys()):
        n_s = len(strata[s])
        floats = {b: targets[b] / total_target * n_s for b in bucket_names}
        floors = {b: int(floats[b]) for b in bucket_names}
        rems = {b: floats[b] - floors[b] for b in bucket_names}
        slack = n_s - sum(floors.values())
        ordered = sorted(bucket_names, key=lambda b: (-rems[b], b))
        per = dict(floors)
        for b in ordered[:slack]:
            per[b] += 1

        idx = 0
        for b in bucket_names:
            assignments[b].extend(strata[s][idx:idx + per[b]])
            idx += per[b]

    # Phase 2: rebalance to exact targets if rounding put us off.
    # Deterministic: move from over-full buckets to under-full ones in
    # fixed bucket-name order, picking the over-full bucket's
    # lexicographically-largest cluster (by rep_pid).
    def deficit(b):
        return targets[b] - len(assignments[b])

    while any(deficit(b) > 0 for b in bucket_names):
        under = next(b for b in bucket_names if deficit(b) > 0)
        over = next(b for b in bucket_names if deficit(b) < 0)
        # Move the cluster with the largest rep_pid from over to under
        # (deterministic; doesn't matter which one, just be consistent).
        assignments[over].sort(key=lambda c: c["rep_pid"])
        moved = assignments[over].pop()
        assignments[under].append(moved)

    for b in bucket_names:
        assignments[b].sort(key=lambda c: c["rep_pid"])

    return assignments


def summarize_strata(label, clusters):
    counter = Counter(c["stratum"] for c in clusters)
    print(f"  {label}  (n={len(clusters)}):")
    for stratum in sorted(counter):
        print(f"    {stratum}: {counter[stratum]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-rebalance", action="store_true",
                    help="Allow re-rolling the splits even if "
                         "puzzles_frozen/ already has files.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute splits and print, but don't write "
                         "files or move puzzles.")
    args = ap.parse_args()

    # Guard against accidental re-roll.
    if FROZEN_DIR.exists() and any(FROZEN_DIR.iterdir()):
        if not args.force_rebalance:
            print(f"ERROR: {FROZEN_DIR} already contains files. The "
                  "frozen set has been locked. Re-rolling would "
                  "invalidate any eval run that has already used it. "
                  "Pass --force-rebalance only if you are sure.",
                  file=sys.stderr)
            sys.exit(2)
        else:
            print(f"WARNING: --force-rebalance set. Existing "
                  f"{FROZEN_DIR} contents will be moved back into "
                  "puzzles/ before re-splitting.", file=sys.stderr)
            for p in FROZEN_DIR.iterdir():
                if p.is_file():
                    shutil.move(str(p), str(PUZZLES_DIR / p.name))

    print(f"Reading puzzles from {PUZZLES_DIR}…")
    clusters = load_clusters()
    print(f"  total files:           {sum(len(c['files']) for c in clusters)}")
    print(f"  content-unique:        {len(clusters)}")

    a2e_leakers, a2e_only, non_a2e = categorize(clusters)
    print(f"  a2e_leakers (A2E ∩ A1):{len(a2e_leakers)}")
    print(f"  a2e_only:              {len(a2e_only)}")
    print(f"  non_a2e (train pool):  {len(non_a2e)}")

    if len(a2e_leakers) != 6:
        print(f"WARNING: expected 6 leakers, got {len(a2e_leakers)}",
              file=sys.stderr)
    if len(a2e_only) != 114:
        print(f"WARNING: expected 114 a2e_only, got {len(a2e_only)}",
              file=sys.stderr)

    targets = {
        "a2e_final_hard": COUNT_A2E_FINAL_HARD,
        "a2e_dev_hard":   COUNT_A2E_DEV_HARD,
        "a2e_train_hard": COUNT_A2E_TRAIN_HARD,
    }
    if sum(targets.values()) != len(a2e_only):
        print(f"ERROR: targets sum to {sum(targets.values())} but "
              f"a2e_only has {len(a2e_only)}", file=sys.stderr)
        sys.exit(3)

    print(f"\nStratified split of a2e_only (seed={SEED}, "
          f"targets={targets})…")
    assignments = stratified_assign(a2e_only, targets, SEED)

    print("\nStratum distribution per bucket:")
    for b in ("a2e_final_hard", "a2e_dev_hard", "a2e_train_hard"):
        summarize_strata(b, assignments[b])

    splits = {
        "seed": SEED,
        "buckets": {
            "a2e_final_hard": [_cluster_record(c) for c in assignments["a2e_final_hard"]],
            "a2e_dev_hard":   [_cluster_record(c) for c in assignments["a2e_dev_hard"]],
            "a2e_train_hard": [_cluster_record(c) for c in assignments["a2e_train_hard"]],
            "a2e_leakers":    [_cluster_record(c) for c in a2e_leakers],
            "train_pool":     [_cluster_record(c) for c in non_a2e],
        },
        "policy": {
            "a2e_leaker_policy": (
                "exclude_from_hard_dev_and_final; "
                "allow_train_only_if_parent_seen_in_A1"
            ),
            "hold_out_unit": "content_cluster_and_all_augmentation_parents",
            "stratify_by": ["size_bucket", "pair_shape_mix", "n_test_pairs"],
        },
    }

    frozen_pids = sorted({
        pid for c in assignments["a2e_final_hard"] for pid in c["pids"]
    })
    frozen_files = sorted({
        f for c in assignments["a2e_final_hard"] for f in c["files"]
    })

    if args.dry_run:
        print("\n--dry-run; not writing any files.")
        print(f"Would lock {len(frozen_pids)} pids ({len(frozen_files)} "
              "physical files) into puzzles_frozen/.")
        return

    SPLITS_DIR.mkdir(exist_ok=True)
    SPLITS_JSON.write_text(json.dumps(splits, indent=2))
    print(f"\nWrote {SPLITS_JSON.relative_to(ROOT.parent)}")

    FROZEN_IDS_TXT.write_text("\n".join(frozen_pids) + "\n")
    print(f"Wrote {FROZEN_IDS_TXT.relative_to(ROOT.parent)} "
          f"({len(frozen_pids)} ids)")

    FROZEN_DIR.mkdir(exist_ok=True)
    moved = 0
    for fname in frozen_files:
        src = PUZZLES_DIR / fname
        dst = FROZEN_DIR / fname
        if not src.exists():
            print(f"WARNING: expected {src} but it is missing — "
                  "split state may be inconsistent.", file=sys.stderr)
            continue
        shutil.move(str(src), str(dst))
        moved += 1
    print(f"Moved {moved} files into {FROZEN_DIR.relative_to(ROOT.parent)}")

    remaining = len(list(PUZZLES_DIR.glob("*.json")))
    print(f"\nFinal state:")
    print(f"  puzzles/        {remaining} files")
    print(f"  puzzles_frozen/ {moved} files")
    print(f"  splits/phase1_splits.json")
    print(f"  splits/frozen_final_eval_ids.txt")


def _cluster_record(c):
    """Slim JSON record for the splits file."""
    return {
        "rep_pid": c["rep_pid"],
        "pids":    c["pids"],
        "sources": c["sources"],
        "files":   c["files"],
        "stratum": list(c["stratum"]),
        "n_train": c["n_train"],
        "n_test":  c["n_test"],
    }


if __name__ == "__main__":
    main()
