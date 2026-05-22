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
PROBE_IDS_FILE = ROOT / "splits" / "phase1_probe_ids.txt"
DATA_SFT_DIR = ROOT / "data_sft"

# The system message that every Phase 1 record carries. The legend
# leverages Qwen's English pretraining instead of forcing the model
# to learn the substrate alphabet by gradient descent from scratch.
SYSTEM_MESSAGE = """Transformation Rule

A RULE encodes one input/output grid transformation.

If input.shape == output.shape, the RULE is a same-shape grid:
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: RULE[r,c] depends only on input[r,c] and output[r,c],
not on neighbors.
Lossless: the output can be fully reconstructed from input + RULE.

If input.shape != output.shape, the RULE is an aggregate text block with sections
in this order: SIZE, BG, PALETTE, ROWS, COLS, BBOX. Sections are separated by
blank lines.
Whole-grid statistics — diagnostic only, not a per-cell reconstruction recipe.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0"""

# Probe set carve-out from train_pool. Same probe puzzles across both
# stages so we can measure (a) "is 1.A literacy locked in?" before
# starting 1.B, and (b) "did 1.B forget the literacy?" after 1.B.
PROBE_SIZE = 50
PROBE_SEED_MULT = 7919  # arbitrary prime, separate from aug seed streams

# Hard-coded from the configs (kept here to avoid a YAML parser dep).
# If you change phase1a/b_config.yaml, mirror here.
STAGE_CONFIG = {
    "1a": {
        "stage_name": "phase1a_substrate_literacy",
        "seed": 42,
        "task_mix": {
            "pair_to_substrate":       0.50,
            "substrate_to_output":     0.50,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
            "dev":   {"d4": True, "color_perms": 1, "pair_subsetting": False},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1a_train.jsonl",
            "dev":      DATA_SFT_DIR / "phase1a_dev.jsonl",
            "probe":    DATA_SFT_DIR / "phase1a_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1a_manifest.json",
        },
    },
    "1b": {
        "stage_name": "phase1b_rule_application",
        "seed": 42,
        "task_mix": {
            "pair_to_substrate":         0.05,
            "substrate_to_output":       0.05,
            "multi_pair_to_rule":        0.35,
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
            "probe":    DATA_SFT_DIR / "phase1b_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1b_manifest.json",
        },
    },
}

# Formats valid only for same-size pairs (need lossless decoder).
SAME_SIZE_ONLY = {"substrate_to_output"}

# Formats that need at least N train pairs *after* subsetting.
MIN_TRAIN_PAIRS = {
    "multi_pair_to_rule":        3,  # >=2 worked + 1 trailing
    "test_substrate_prediction": 2,
    "direct_output_grid":        2,
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
        f"RULE:\n"
    )
    target = render_substrate(pair["input"], pair["output"])
    return user, target


def fmt_substrate_to_output(puzzle, rng):
    """substrate_to_output: same-size pairs only. Show input + rule,
    target the output."""
    candidates = [p for p in puzzle["train"] if is_same_size(p)]
    if not candidates:
        return None
    pair = rng.choice(candidates)
    sub = encode(pair["input"], pair["output"])
    user = (
        f"INPUT:\n{grid_to_str(pair['input'])}\n\n"
        f"RULE:\n{format_grid(sub)}\n\n"
        f"OUTPUT:\n"
    )
    target = grid_to_str(pair["output"])
    return user, target


def fmt_multi_pair_to_rule(puzzle, rng, trailing_idx=None):
    """N-1 worked pairs (INPUT + OUTPUT + RULE) plus 1 trailing pair
    (INPUT + OUTPUT, no RULE) → produce the trailing pair's RULE.

    Style C: no COLD/P prefixes. Structure tells the model which pair
    is to-produce: it's the only one missing its RULE content.

    If `trailing_idx` is provided, that position becomes the trailing
    one (used by the generator to deterministically rotate through all
    positions). If None, picks uniformly at random.
    """
    if len(puzzle["train"]) < 3:
        return None
    n = len(puzzle["train"])
    if trailing_idx is None:
        trailing_idx = rng.randrange(n)
    user_lines = []
    for i, pair in enumerate(puzzle["train"]):
        if i == trailing_idx:
            continue
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"RULE:\n{render_substrate(pair['input'], pair['output'])}")
    trailing = puzzle["train"][trailing_idx]
    user_lines.append(f"INPUT:\n{grid_to_str(trailing['input'])}")
    user_lines.append(f"OUTPUT:\n{grid_to_str(trailing['output'])}")
    user = "\n\n".join(user_lines) + "\n\nRULE:\n"
    target = render_substrate(trailing["input"], trailing["output"])
    return user, target


def fmt_test_substrate_prediction(puzzle, rng):
    """test_substrate_prediction (internal name kept): worked train pairs
    with their rules + test INPUT only. Target = test rule.

    Style C — no TEST or P prefixes. The test pair is identifiable by
    structure: it's the trailing pair missing both its OUTPUT and its
    RULE content.
    """
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_idx = rng.randrange(len(puzzle["test"]))
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for pair in puzzle["train"]:
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"RULE:\n{render_substrate(pair['input'], pair['output'])}")
    user_lines.append(f"INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nRULE:\n"
    target = render_substrate(test_pair["input"], test_pair["output"])
    return user, target, test_idx


def fmt_direct_output_grid(puzzle, rng):
    """direct_output_grid: train pairs (INPUT, OUTPUT) + test INPUT.
    Target = test OUTPUT grid. No rules anywhere in this format.
    """
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_idx = rng.randrange(len(puzzle["test"]))
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for pair in puzzle["train"]:
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
    user_lines.append(f"INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nOUTPUT:\n"
    target = grid_to_str(test_pair["output"])
    return user, target, test_idx


FORMAT_FNS = {
    "pair_to_substrate":         fmt_pair_to_substrate,
    "substrate_to_output":       fmt_substrate_to_output,
    "multi_pair_to_rule":        fmt_multi_pair_to_rule,
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
                bucket, stage_name, rng, trailing_idx=None):
    fn = FORMAT_FNS[format_name]
    if format_name == "multi_pair_to_rule":
        out = fn(variant_puzzle, rng, trailing_idx=trailing_idx)
    else:
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
    if format_name == "multi_pair_to_rule" and trailing_idx is not None:
        record["provenance"]["trailing_pair_index"] = trailing_idx
    return record


def generate_for_bucket(bucket_name, cluster_list, aug_cfg, stage_cfg,
                        master_seed, max_per_puzzle):
    """Generate records for one bucket using target-driven sampling.

    Two-phase algorithm:
      1. Enumerate all (cluster, augmented_variant) items with their
         eligible-format sets.
      2. For each format independently, sample target_ratio*total_items
         from that format's eligible pool. The same (cluster, variant)
         can be drawn by multiple formats — each yields a different
         record (different conversational framing).

    This hits target mix ratios cleanly, even when single-train-pair
    puzzles are only eligible for pair_to_substrate. Previously those
    puzzles dragged the mix because the per-variant sampler used
    "eligible-only" weights, which over-counted pair_to_substrate.
    """
    # Phase 1: enumerate all variants with eligibility info.
    items = []
    base_count = 0   # number of (cluster, variant) tuples; denominator for mix
    skip_counter = Counter()

    for cluster in cluster_list:
        rep_pid = cluster["rep_pid"]
        sources = cluster["sources"]
        fname = cluster["files"][0]
        path = PUZZLES_DIR / fname
        if not path.exists():
            skip_counter["file_missing"] += 1
            continue
        puzzle = load_puzzle(path)

        per_puzzle_seed = (master_seed * 1000003 + sum(ord(c) for c in rep_pid)) & 0x7FFFFFFF
        rng = random.Random(per_puzzle_seed)

        variants = augmentation_variants(puzzle, aug_cfg, rng)
        if len(variants) > max_per_puzzle:
            variants = rng.sample(variants, max_per_puzzle)

        for variant_puzzle, prov_aug in variants:
            eligible = set(eligible_formats(variant_puzzle, stage_cfg["task_mix"]))
            if not eligible:
                skip_counter["no_eligible_format"] += 1
                continue
            base_count += 1  # count one (cluster, variant) tuple
            base_item = {
                "cluster_rep_pid": rep_pid,
                "cluster_sources": sources,
                "variant_puzzle":  variant_puzzle,
                "prov_aug":        prov_aug,
                "eligible":        eligible,
                "trailing_idx":    None,
            }
            # multi_pair_to_rule: expand into one candidate per
            # trailing position so all positions get systematic coverage.
            # The expansion only grows multi_pair_to_rule's candidate pool;
            # it does NOT inflate the budget for other formats (the format
            # target is computed from base_count, not from len(items)).
            if "multi_pair_to_rule" in eligible:
                n_train = len(variant_puzzle["train"])
                for t_idx in range(n_train):
                    items.append({**base_item,
                                  "eligible": {"multi_pair_to_rule"},
                                  "trailing_idx": t_idx})
                non_multi = eligible - {"multi_pair_to_rule"}
                if non_multi:
                    items.append({**base_item, "eligible": non_multi})
            else:
                items.append(base_item)

    # Phase 2: per-format target-driven sampling.
    # Targets are proportional to base_count (number of (cluster, variant)
    # tuples), not to len(items) which is inflated by the multi_pair
    # rotation expansion. This keeps the mix ratios honest: 5% / 5% / 35%
    # / 40% / 15% means 5/5/35/40/15 share of the OUTPUT records, not
    # 5/5/35/40/15 of an inflated denominator.
    total_items = len(items)
    format_targets = {
        fmt: int(round(ratio * base_count))
        for fmt, ratio in stage_cfg["task_mix"].items()
    }
    pool_sizes = {fmt: 0 for fmt in stage_cfg["task_mix"]}
    for it in items:
        for fmt in it["eligible"]:
            if fmt in pool_sizes:
                pool_sizes[fmt] += 1

    records = []
    fmt_counter = Counter()
    rng_pick = random.Random(master_seed + 99)

    for fmt, target in format_targets.items():
        eligible_items = [it for it in items if fmt in it["eligible"]]
        if len(eligible_items) < target:
            skip_counter[f"{fmt}_pool_short_by"] = target - len(eligible_items)
            chosen = eligible_items
        else:
            chosen = rng_pick.sample(eligible_items, target)
        for it in chosen:
            rec = make_record(
                format_name=fmt,
                variant_puzzle=it["variant_puzzle"],
                prov_aug=it["prov_aug"],
                rep_pid=it["cluster_rep_pid"],
                sources=it["cluster_sources"],
                bucket=bucket_name,
                stage_name=stage_cfg["stage_name"],
                rng=rng_pick,
                trailing_idx=it.get("trailing_idx"),
            )
            if rec is None:
                skip_counter[f"{fmt}_returned_none"] += 1
                continue
            records.append(rec)
            fmt_counter[fmt] += 1

    skip_counter["_pool_sizes"] = pool_sizes
    skip_counter["_n_variants"] = total_items
    return records, fmt_counter, skip_counter


def select_probe_clusters(train_pool: list, seed: int) -> list:
    """Deterministically sample PROBE_SIZE clusters from train_pool.

    Uses a seed stream independent of the augmentation seeds so the
    probe selection is stable even if we change augmentation parameters
    later. Sorted by rep_pid first for stability across Python random
    implementations.
    """
    rng = random.Random(seed * PROBE_SEED_MULT)
    sorted_pool = sorted(train_pool, key=lambda c: c["rep_pid"])
    if PROBE_SIZE > len(sorted_pool):
        raise ValueError(
            f"train_pool has only {len(sorted_pool)} clusters, "
            f"can't carve probe of {PROBE_SIZE}"
        )
    return rng.sample(sorted_pool, PROBE_SIZE)


def generate_probe_records(probe_clusters, stage_cfg, master_seed):
    """One record per (cluster, eligible format) using identity
    augmentation. No D4, no color perm, no pair subsetting.

    For multi_pair_to_rule the probe uses trailing_idx=0 deterministically
    (one position is enough for the gate decision; full coverage is a
    training concern, not an evaluation concern).
    """
    records = []
    fmt_counter = Counter()
    skip_counter = Counter()
    rng = random.Random(master_seed * 31 + 7)

    for cluster in probe_clusters:
        rep_pid = cluster["rep_pid"]
        sources = cluster["sources"]
        path = PUZZLES_DIR / cluster["files"][0]
        if not path.exists():
            skip_counter["file_missing"] += 1
            continue
        puzzle = load_puzzle(path)
        eligible = eligible_formats(puzzle, stage_cfg["task_mix"])
        for fmt in eligible:
            trailing_idx = 0 if fmt == "multi_pair_to_rule" else None
            rec = make_record(
                format_name=fmt,
                variant_puzzle=puzzle,
                prov_aug={
                    "d4_op": "identity",
                    "color_perm_seed": None,
                    "pair_subset": list(range(len(puzzle["train"]))),
                },
                rep_pid=rep_pid,
                sources=sources,
                bucket="probe",
                stage_name=stage_cfg["stage_name"],
                rng=rng,
                trailing_idx=trailing_idx,
            )
            if rec is None:
                skip_counter[f"{fmt}_returned_none"] += 1
                continue
            records.append(rec)
            fmt_counter[fmt] += 1
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
    PROBE_IDS_FILE.parent.mkdir(exist_ok=True)

    # Probe carve-out: PROBE_SIZE clusters from train_pool, held out
    # from BOTH stages' training. Used to measure stage-end literacy
    # (gate between 1.A and 1.B; forgetting check after 1.B).
    probe_clusters = select_probe_clusters(splits["buckets"]["train_pool"], seed)
    probe_pids = {c["rep_pid"] for c in probe_clusters}

    # If the probe id list doesn't exist yet, write it. If it does,
    # verify it matches what we just computed (catches accidental seed
    # changes).
    expected_ids = sorted(probe_pids)
    if PROBE_IDS_FILE.exists():
        existing_ids = sorted(PROBE_IDS_FILE.read_text().strip().split("\n"))
        if existing_ids != expected_ids:
            print(f"ERROR: probe ids drifted from {PROBE_IDS_FILE}. "
                  f"Existing {len(existing_ids)} vs computed "
                  f"{len(expected_ids)}. Refusing to regenerate — "
                  "remove the file manually if you really mean to "
                  "re-roll the probe.", file=sys.stderr)
            sys.exit(4)
    else:
        PROBE_IDS_FILE.write_text("\n".join(expected_ids) + "\n")
        print(f"Wrote {PROBE_IDS_FILE.relative_to(REPO)} "
              f"({len(expected_ids)} ids)")

    train_pool_minus_probe = [
        c for c in splits["buckets"]["train_pool"]
        if c["rep_pid"] not in probe_pids
    ]

    # Train bucket = (train_pool minus probe) + a2e_train_hard + leakers.
    # Leakers are allowed in train because A1 is fully in train anyway
    # (their parent puzzles are seen).
    train_clusters = (
        train_pool_minus_probe
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
    print(f"Train clusters: {len(train_clusters)} "
          f"(train_pool {len(train_pool_minus_probe)} + "
          f"a2e_train_hard {len(splits['buckets']['a2e_train_hard'])} + "
          f"leakers {len(splits['buckets']['a2e_leakers'])})")
    print(f"Dev clusters:   {len(dev_clusters)}")
    print(f"Probe clusters: {len(probe_clusters)} "
          f"(carved from train_pool, held out from both stages' train)")

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

    print(f"\nGenerating probe (identity aug, every (puzzle, format))…")
    probe_records, probe_fmt, probe_skip = generate_probe_records(
        probe_clusters, cfg, master_seed=seed,
    )
    print(f"  {len(probe_records)} records")
    for fmt, n in sorted(probe_fmt.items()):
        print(f"    {fmt}: {n}")
    if probe_skip:
        print(f"  skips: {dict(probe_skip)}")

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
    out_probe = cfg["out_files"]["probe"]
    out_manifest = cfg["out_files"]["manifest"]

    if args.sample_only:
        out_train = out_train.with_name(out_train.stem + "_sample.jsonl")
        out_dev = out_dev.with_name(out_dev.stem + "_sample.jsonl")
        out_probe = out_probe.with_name(out_probe.stem + "_sample.jsonl")
        out_manifest = out_manifest.with_name(out_manifest.stem + "_sample.json")

    with out_train.open("w") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out_dev.open("w") as f:
        for r in dev_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out_probe.open("w") as f:
        for r in probe_records:
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
        "probe": {
            "file": str(out_probe.relative_to(REPO)),
            "n_records": len(probe_records),
            "n_clusters": len(probe_clusters),
            "format_counts": dict(probe_fmt),
            "skipped": dict(probe_skip),
            "ids_file": str(PROBE_IDS_FILE.relative_to(REPO)),
        },
    }
    out_manifest.write_text(json.dumps(manifest, indent=2))

    print(f"\nWrote:")
    print(f"  {out_train.relative_to(REPO)}")
    print(f"  {out_dev.relative_to(REPO)}")
    print(f"  {out_probe.relative_to(REPO)}")
    print(f"  {out_manifest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
