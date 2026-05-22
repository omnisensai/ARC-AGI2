#!/usr/bin/env python3
"""Phase 1 SFT dataset generator (1.A or 1.B, selected by --stage).

Reads:
  Fine Tune Run 2/phase1a_config.yaml (or 1b)
  Fine Tune Run 2/splits/phase1_splits.json
  Fine Tune Run 2/puzzles/*.json

Writes:
  Fine Tune Run 2/data_sft/phase1{a,b}_train.jsonl
  Fine Tune Run 2/data_sft/phase1{a,b}_dev.jsonl
  Fine Tune Run 2/data_sft/phase1{a,b}_manifest.json

Usage:
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage 1a
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage 1b --sample-only
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage 1a --max-per-puzzle 4
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Repo root for substrate import
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from substrate import encode_auto, encode, decode, format_grid  # noqa: E402


PUZZLES_DIR = ROOT / "puzzles"
SPLITS_FILE = ROOT / "splits" / "phase1_splits.json"
DATA_SFT_DIR = ROOT / "data_sft"
SYSTEM_MESSAGE = "Transformation Rule"

# Hard-coded from the configs (kept here to avoid a YAML parser dep).
# If you change phase1a/b_config.yaml, mirror here.
STAGE_CONFIG = {
    "1a": {
        "stage_name": "phase1a_substrate_literacy",
        "seed": 42,
        "task_mix": {
            "pair_to_substrate":       0.40,
            "substrate_to_output":     0.35,
            "all_pairs_to_substrates": 0.25,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
            "dev":   {"d4": True, "color_perms": 1, "pair_subsetting": False},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1a_train.jsonl",
            "dev":      DATA_SFT_DIR / "phase1a_dev.jsonl",
            "manifest": DATA_SFT_DIR / "phase1a_manifest.json",
        },
    },
    "1b": {
        "stage_name": "phase1b_rule_application",
        "seed": 42,
        "task_mix": {
            "pair_to_substrate":         0.05,
            "substrate_to_output":       0.05,
            "all_pairs_to_substrates":   0.10,
            "cold_pair_to_substrate":    0.25,
            "test_substrate_prediction": 0.40,
            "direct_output_grid":        0.15,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
            "dev":   {"d4": True, "color_perms": 1, "pair_subsetting": False},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1b_train.jsonl",
            "dev":      DATA_SFT_DIR / "phase1b_dev.jsonl",
            "manifest": DATA_SFT_DIR / "phase1b_manifest.json",
        },
    },
}

# Formats valid only for same-size pairs (need lossless decoder).
SAME_SIZE_ONLY = {"substrate_to_output"}

# Formats that need at least N train pairs *after* subsetting.
MIN_TRAIN_PAIRS = {
    "cold_pair_to_substrate":    3,  # >=2 worked + 1 cold
    "test_substrate_prediction": 2,
    "direct_output_grid":        2,
    "all_pairs_to_substrates":   2,
}


# ---------------------------------------------------------------------------
# Grid + puzzle helpers

def parse_grid(s: str):
    return [[int(c) for c in row] for row in s.split("\n")]


def grid_to_str(g):
    return "\n".join("".join(str(c) for c in row) for row in g)


def load_puzzle(path: Path) -> dict:
    """Return the puzzle as dict with grids parsed to list[list[int]]."""
    raw = json.loads(path.read_text())
    return {
        "train": [{"input": parse_grid(p["input"]),
                   "output": parse_grid(p["output"])} for p in raw["train"]],
        "test":  [{"input": parse_grid(p["input"]),
                   "output": parse_grid(p["output"])} for p in raw["test"]],
    }


# ---------------------------------------------------------------------------
# D4 + color permutation augmentations (rule-preserving)

def _rot90(g):
    return [list(row) for row in zip(*g[::-1])]


def _flip_h(g):
    return [row[::-1] for row in g]


D4_OPS = {
    "identity": lambda g: [row[:] for row in g],
    "rot90":    lambda g: _rot90(g),
    "rot180":   lambda g: _rot90(_rot90(g)),
    "rot270":   lambda g: _rot90(_rot90(_rot90(g))),
    "flip_h":   lambda g: _flip_h(g),
    "flip_v":   lambda g: _flip_h(_rot90(_rot90(g))),
    "transpose": lambda g: [list(row) for row in zip(*g)],
    "anti_transpose": lambda g: [list(row) for row in zip(*[r[::-1] for r in g[::-1]])],
}


def apply_d4(puzzle: dict, op_name: str) -> dict:
    op = D4_OPS[op_name]
    return {
        "train": [{"input": op(p["input"]), "output": op(p["output"])}
                  for p in puzzle["train"]],
        "test":  [{"input": op(p["input"]), "output": op(p["output"])}
                  for p in puzzle["test"]],
    }


def random_color_perm(rng) -> list:
    """Random non-identity permutation of [0..9]."""
    while True:
        p = list(range(10))
        rng.shuffle(p)
        if p != list(range(10)):
            return p


def apply_color_perm(puzzle: dict, perm: list) -> dict:
    def m(g):
        return [[perm[c] for c in row] for row in g]
    return {
        "train": [{"input": m(p["input"]), "output": m(p["output"])}
                  for p in puzzle["train"]],
        "test":  [{"input": m(p["input"]), "output": m(p["output"])}
                  for p in puzzle["test"]],
    }


def apply_pair_subset(puzzle: dict, subset_indices: tuple) -> dict:
    """Keep only the listed train pairs; test pairs unchanged."""
    return {
        "train": [puzzle["train"][i] for i in subset_indices],
        "test":  [p for p in puzzle["test"]],
    }


# ---------------------------------------------------------------------------
# Augmentation enumeration per puzzle

def augmentation_variants(puzzle: dict, aug_cfg: dict, rng) -> list:
    """Return a list of (variant_puzzle, prov_dict) tuples.

    Each variant has: d4_op applied, color_perm applied (or identity),
    and optionally a pair subset. Order is deterministic given rng.
    """
    variants = []
    d4_ops = list(D4_OPS.keys()) if aug_cfg.get("d4") else ["identity"]
    n_color_perms = aug_cfg.get("color_perms", 0)

    # Pre-sample color permutations so they're shared across D4 ops
    color_perms = [(None, list(range(10)))]  # identity
    for i in range(n_color_perms):
        color_perms.append((f"cp{i}", random_color_perm(rng)))

    # Pair-subset draws (deterministic). Skip when disabled or when
    # the puzzle has only 1 train pair.
    n_train = len(puzzle["train"])
    pair_subsets = [tuple(range(n_train))]
    if aug_cfg.get("pair_subsetting") and n_train >= 2:
        lo = aug_cfg.get("pair_subset_min", 1)
        hi = min(aug_cfg.get("pair_subset_max", n_train), n_train)
        # 2 random subsets per puzzle, plus the "all pairs" variant
        for _ in range(2):
            k = rng.randint(max(lo, 1), hi)
            idxs = tuple(sorted(rng.sample(range(n_train), k)))
            if idxs != tuple(range(n_train)) and idxs not in pair_subsets:
                pair_subsets.append(idxs)

    for d4_name in d4_ops:
        for cp_label, perm in color_perms:
            for subset in pair_subsets:
                p1 = apply_d4(puzzle, d4_name)
                p2 = apply_color_perm(p1, perm)
                p3 = apply_pair_subset(p2, subset)
                prov = {
                    "d4_op": d4_name,
                    "color_perm_seed": cp_label,
                    "pair_subset": list(subset),
                }
                variants.append((p3, prov))
    return variants


# ---------------------------------------------------------------------------
# Substrate rendering

def render_substrate(inp, out) -> str:
    """encode_auto returns Substrate (list-of-lists) for same-size and str
    for diff-size. This wrapper always returns a string."""
    s = encode_auto(inp, out)
    return s if isinstance(s, str) else format_grid(s)


def is_same_size(pair) -> bool:
    inp, out = pair["input"], pair["output"]
    return len(inp) == len(out) and len(inp[0]) == len(out[0])


# ---------------------------------------------------------------------------
# Format renderers — each returns (user_content, assistant_content)

def fmt_pair_to_substrate(puzzle, rng):
    """pair_to_substrate: pick one train pair, encode it."""
    pair = rng.choice(puzzle["train"])
    user = (
        f"INPUT:\n{grid_to_str(pair['input'])}\n\n"
        f"OUTPUT:\n{grid_to_str(pair['output'])}\n\n"
        f"SUBSTRATE:\n"
    )
    target = render_substrate(pair["input"], pair["output"])
    return user, target


def fmt_substrate_to_output(puzzle, rng):
    """substrate_to_output: same-size pairs only. Show input + substrate,
    target the output."""
    candidates = [p for p in puzzle["train"] if is_same_size(p)]
    if not candidates:
        return None
    pair = rng.choice(candidates)
    sub = encode(pair["input"], pair["output"])
    user = (
        f"INPUT:\n{grid_to_str(pair['input'])}\n\n"
        f"SUBSTRATE:\n{format_grid(sub)}\n\n"
        f"OUTPUT:\n"
    )
    target = grid_to_str(pair["output"])
    return user, target


def fmt_all_pairs_to_substrates(puzzle, rng):
    """all_pairs_to_substrates: show all train pairs as (input, output),
    target the substrates per pair."""
    if len(puzzle["train"]) < 2:
        return None
    user_lines = []
    target_lines = []
    for i, pair in enumerate(puzzle["train"], start=1):
        user_lines.append(f"P{i} INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"P{i} OUTPUT:\n{grid_to_str(pair['output'])}")
        target_lines.append(f"P{i} SUBSTRATE:\n{render_substrate(pair['input'], pair['output'])}")
    user = "\n\n".join(user_lines) + "\n\nSUBSTRATES:\n"
    target = "\n\n".join(target_lines)
    return user, target


def fmt_cold_pair_to_substrate(puzzle, rng):
    """cold_pair_to_substrate: pick one pair as the cold pair, the rest
    are shown as worked (input + output + substrate)."""
    if len(puzzle["train"]) < 3:
        return None
    n = len(puzzle["train"])
    cold_idx = rng.randrange(n)
    user_lines = []
    pcount = 0
    for i, pair in enumerate(puzzle["train"]):
        if i == cold_idx:
            continue
        pcount += 1
        user_lines.append(f"P{pcount} INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"P{pcount} OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"P{pcount} SUBSTRATE:\n{render_substrate(pair['input'], pair['output'])}")
    cold = puzzle["train"][cold_idx]
    user_lines.append(f"COLD INPUT:\n{grid_to_str(cold['input'])}")
    user_lines.append(f"COLD OUTPUT:\n{grid_to_str(cold['output'])}")
    user = "\n\n".join(user_lines) + "\n\nCOLD SUBSTRATE:\n"
    target = render_substrate(cold["input"], cold["output"])
    return user, target


def fmt_test_substrate_prediction(puzzle, rng):
    """test_substrate_prediction: worked train pairs (input+output+substrate)
    + test input. Target = test substrate."""
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_idx = rng.randrange(len(puzzle["test"]))
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for i, pair in enumerate(puzzle["train"], start=1):
        user_lines.append(f"P{i} INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"P{i} OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"P{i} SUBSTRATE:\n{render_substrate(pair['input'], pair['output'])}")
    user_lines.append(f"TEST INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nTEST SUBSTRATE:\n"
    target = render_substrate(test_pair["input"], test_pair["output"])
    return user, target, test_idx


def fmt_direct_output_grid(puzzle, rng):
    """direct_output_grid: train pairs (input, output) + test input.
    Target = test output grid."""
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_idx = rng.randrange(len(puzzle["test"]))
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for i, pair in enumerate(puzzle["train"], start=1):
        user_lines.append(f"P{i} INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"P{i} OUTPUT:\n{grid_to_str(pair['output'])}")
    user_lines.append(f"TEST INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nOUTPUT:\n"
    target = grid_to_str(test_pair["output"])
    return user, target, test_idx


FORMAT_FNS = {
    "pair_to_substrate":         fmt_pair_to_substrate,
    "substrate_to_output":       fmt_substrate_to_output,
    "all_pairs_to_substrates":   fmt_all_pairs_to_substrates,
    "cold_pair_to_substrate":    fmt_cold_pair_to_substrate,
    "test_substrate_prediction": fmt_test_substrate_prediction,
    "direct_output_grid":        fmt_direct_output_grid,
}


def eligible_formats(variant_puzzle, task_mix):
    """Which formats in task_mix can this augmented puzzle support?"""
    eligible = []
    n_train = len(variant_puzzle["train"])
    has_test = bool(variant_puzzle["test"])
    has_same_size_train = any(is_same_size(p) for p in variant_puzzle["train"])
    for fmt, weight in task_mix.items():
        if weight <= 0:
            continue
        if fmt == "substrate_to_output" and not has_same_size_train:
            continue
        if fmt in MIN_TRAIN_PAIRS and n_train < MIN_TRAIN_PAIRS[fmt]:
            continue
        if fmt in ("test_substrate_prediction", "direct_output_grid") and not has_test:
            continue
        eligible.append(fmt)
    return eligible


def sample_format(eligible, task_mix, rng):
    """Sample a format from `eligible` weighted by task_mix."""
    weights = [task_mix[f] for f in eligible]
    return rng.choices(eligible, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Generation loop

def make_record(format_name, variant_puzzle, prov_aug, rep_pid, sources,
                bucket, stage_name, rng):
    fn = FORMAT_FNS[format_name]
    out = fn(variant_puzzle, rng)
    if out is None:
        return None

    if format_name in ("test_substrate_prediction", "direct_output_grid"):
        user, target, test_pair_index = out
    else:
        user, target = out
        test_pair_index = None

    record = {
        "messages": [
            {"role": "system",    "content": SYSTEM_MESSAGE},
            {"role": "user",      "content": user},
            {"role": "assistant", "content": target},
        ],
        "provenance": {
            "format": format_name,
            "stage":  stage_name,
            "bucket": bucket,
            "puzzle_id": rep_pid,
            "sources": sources,
            **prov_aug,
        },
    }
    if test_pair_index is not None:
        record["provenance"]["test_pair_index"] = test_pair_index
    return record


def generate_for_bucket(bucket_name, cluster_list, aug_cfg, stage_cfg,
                        master_seed, max_per_puzzle):
    """Generate records for one bucket. Returns list of records."""
    records = []
    fmt_counter = Counter()
    skip_counter = Counter()

    for cluster in cluster_list:
        rep_pid = cluster["rep_pid"]
        sources = cluster["sources"]
        # Use the first available source file for this cluster — they're
        # all the same canonical content.
        fname = cluster["files"][0]
        path = PUZZLES_DIR / fname
        if not path.exists():
            skip_counter["file_missing"] += 1
            continue
        puzzle = load_puzzle(path)

        # Deterministic per-puzzle RNG seeded by (master_seed, pid).
        per_puzzle_seed = (master_seed * 1000003 + sum(ord(c) for c in rep_pid)) & 0x7FFFFFFF
        rng = random.Random(per_puzzle_seed)

        variants = augmentation_variants(puzzle, aug_cfg, rng)
        # Cap variants per puzzle to keep dataset size manageable.
        if len(variants) > max_per_puzzle:
            variants = rng.sample(variants, max_per_puzzle)

        for variant_puzzle, prov_aug in variants:
            eligible = eligible_formats(variant_puzzle, stage_cfg["task_mix"])
            if not eligible:
                skip_counter["no_eligible_format"] += 1
                continue
            fmt_name = sample_format(eligible, stage_cfg["task_mix"], rng)
            rec = make_record(
                format_name=fmt_name,
                variant_puzzle=variant_puzzle,
                prov_aug=prov_aug,
                rep_pid=rep_pid,
                sources=sources,
                bucket=bucket_name,
                stage_name=stage_cfg["stage_name"],
                rng=rng,
            )
            if rec is None:
                skip_counter[f"{fmt_name}_returned_none"] += 1
                continue
            records.append(rec)
            fmt_counter[fmt_name] += 1

    return records, fmt_counter, skip_counter


def augmentation_rank(prov: dict) -> int:
    """Difficulty rank of an augmented variant.

      0: identity, no color perm (closest to original surface form)
      1: identity + color perm  (palette change, spatial unchanged)
      2: D4 + no color perm     (spatial change, palette unchanged)
      3: D4 + color perm        (both)

    Pair-subsetting is intentionally NOT in the rank — it changes the
    puzzle's effective pair count, not its surface form. Curriculum is
    about surface-form difficulty, not example coverage.
    """
    has_d4 = prov.get("d4_op", "identity") != "identity"
    has_color = prov.get("color_perm_seed") is not None
    return (2 if has_d4 else 0) + (1 if has_color else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["1a", "1b"], required=True)
    ap.add_argument("--sample-only", action="store_true",
                    help="Generate ~50 examples per bucket for review.")
    ap.add_argument("--max-per-puzzle", type=int, default=24,
                    help="Cap augmented variants per puzzle. Default 24.")
    ap.add_argument("--curriculum", choices=["sort", "shuffle"], default="sort",
                    help="train.jsonl ordering. 'sort' (default) orders by "
                         "augmentation difficulty rank (identity -> color -> "
                         "D4 -> combined), with deterministic shuffle within "
                         "each rank. 'shuffle' does a single global shuffle.")
    args = ap.parse_args()

    cfg = STAGE_CONFIG[args.stage]
    splits = json.loads(SPLITS_FILE.read_text())
    seed = cfg["seed"]

    DATA_SFT_DIR.mkdir(exist_ok=True)

    # Train bucket = train_pool + a2e_train_hard (+ leakers per policy)
    # Leakers are included in train: the policy says "allow train only if
    # parent seen in A1" which IS the case (A1 stays fully in train).
    train_clusters = (
        splits["buckets"]["train_pool"]
        + splits["buckets"]["a2e_train_hard"]
        + splits["buckets"]["a2e_leakers"]
    )
    dev_clusters = splits["buckets"]["a2e_dev_hard"]

    if args.sample_only:
        rng = random.Random(seed)
        train_clusters = rng.sample(train_clusters, min(20, len(train_clusters)))
        dev_clusters = rng.sample(dev_clusters, min(5, len(dev_clusters)))
        args.max_per_puzzle = 3

    print(f"Stage: {cfg['stage_name']}  seed={seed}  "
          f"max_per_puzzle={args.max_per_puzzle}")
    print(f"Train clusters: {len(train_clusters)}")
    print(f"Dev clusters:   {len(dev_clusters)}")

    print(f"\nGenerating train…")
    train_records, train_fmt, train_skip = generate_for_bucket(
        bucket_name="train",
        cluster_list=train_clusters,
        aug_cfg=cfg["augment"]["train"],
        stage_cfg=cfg,
        master_seed=seed,
        max_per_puzzle=args.max_per_puzzle,
    )
    print(f"  {len(train_records)} records")
    for fmt, n in sorted(train_fmt.items()):
        print(f"    {fmt}: {n} ({100*n/len(train_records):.1f}%)")
    if train_skip:
        print(f"  skips: {dict(train_skip)}")

    print(f"\nGenerating dev…")
    dev_records, dev_fmt, dev_skip = generate_for_bucket(
        bucket_name="dev",
        cluster_list=dev_clusters,
        aug_cfg=cfg["augment"]["dev"],
        stage_cfg=cfg,
        master_seed=seed + 1,  # different aug stream for dev
        max_per_puzzle=args.max_per_puzzle,
    )
    print(f"  {len(dev_records)} records")
    for fmt, n in sorted(dev_fmt.items()):
        print(f"    {fmt}: {n} ({100*n/len(dev_records):.1f}%)")
    if dev_skip:
        print(f"  skips: {dict(dev_skip)}")

    # Order the train file. Two modes:
    #
    #   sort     curriculum-by-augmentation-difficulty (default). Group
    #            records by augmentation rank 0..3, shuffle within each
    #            rank, then concatenate. Easier surface forms (identity,
    #            color-only) come first; harder (D4, D4+color) come last.
    #            For the first epoch (the one that matters in our SFT
    #            regime), the trainer sees the curriculum order. Most
    #            trainers reshuffle on epoch 2+, which doesn't hurt us.
    #
    #   shuffle  single global shuffle. Status quo, no curriculum.
    rng_shuf = random.Random(seed + 2)
    if args.curriculum == "sort":
        by_rank = defaultdict(list)
        for r in train_records:
            by_rank[augmentation_rank(r["provenance"])].append(r)
        train_records = []
        for rank in (0, 1, 2, 3):
            rng_shuf.shuffle(by_rank[rank])
            train_records.extend(by_rank[rank])
        rank_counts = {r: len(by_rank[r]) for r in (0, 1, 2, 3)}
    else:
        rng_shuf.shuffle(train_records)
        rank_counts = None

    out_train = cfg["out_files"]["train"]
    out_dev = cfg["out_files"]["dev"]
    out_manifest = cfg["out_files"]["manifest"]

    if args.sample_only:
        out_train = out_train.with_name(out_train.stem + "_sample.jsonl")
        out_dev = out_dev.with_name(out_dev.stem + "_sample.jsonl")
        out_manifest = out_manifest.with_name(out_manifest.stem + "_sample.json")

    with out_train.open("w") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out_dev.open("w") as f:
        for r in dev_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "stage": cfg["stage_name"],
        "seed": seed,
        "max_per_puzzle": args.max_per_puzzle,
        "sample_only": args.sample_only,
        "curriculum": args.curriculum,
        "train": {
            "file": str(out_train.relative_to(REPO)),
            "n_records": len(train_records),
            "n_clusters": len(train_clusters),
            "format_counts": dict(train_fmt),
            "augmentation_rank_counts": rank_counts,
            "skipped": dict(train_skip),
        },
        "dev": {
            "file": str(out_dev.relative_to(REPO)),
            "n_records": len(dev_records),
            "n_clusters": len(dev_clusters),
            "format_counts": dict(dev_fmt),
            "skipped": dict(dev_skip),
        },
    }
    out_manifest.write_text(json.dumps(manifest, indent=2))

    print(f"\nWrote:")
    print(f"  {out_train.relative_to(REPO)}")
    print(f"  {out_dev.relative_to(REPO)}")
    print(f"  {out_manifest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
