#!/usr/bin/env python3
"""Phase 1 SFT dataset generator — three-stage substrate-split curriculum.

Stages:
  same   — same-dimensions T grids only. Trained from base Qwen.
           Records only contain transformations where input.shape == output.shape.
           System prompt describes the same-dimensions alphabet only.
  diff   — diff-dimensions T text blocks only. Trained from the `same` LoRA.
           System prompt now describes both alphabets so the model retains
           same-dimensions while learning diff-dimensions.
  mixed  — both alphabets, full ARC puzzle framing. Trained from the `diff`
           LoRA. System prompt adds "puzzles have multiple pairs sharing one
           rule" — sets up rule-transfer reasoning explicitly.

Reads:
  Fine Tune Run 2/splits/phase1_splits.json
  Fine Tune Run 2/puzzles/*.json

Writes (per stage in {same, diff, mixed}):
  Fine Tune Run 2/data_sft/phase1_<stage>_train.jsonl
  Fine Tune Run 2/data_sft/phase1_<stage>_dev.jsonl
  Fine Tune Run 2/data_sft/phase1_<stage>_probe.jsonl
  Fine Tune Run 2/data_sft/phase1_<stage>_manifest.json

Usage:
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage same
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage diff
  python3 "Fine Tune Run 2/build_phase1_dataset.py" --stage mixed
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
API_EVAL_IDS_FILE = ROOT / "splits" / "api_eval_ids.txt"
DATA_SFT_DIR = ROOT / "data_sft"


# ---------------------------------------------------------------------------
# Per-stage system messages.
#
# SAME prompt: only describes the same-dimensions T-grid alphabet. No puzzle-
# level framing yet, no diff-dimensions section. The model in this stage
# only sees same-dimensions records — telling it more would be irrelevant
# context.
#
# DIFF prompt: covers both alphabets (same + diff). The records in this
# stage all target diff-dimensions T blocks, but the prior 'same' LoRA
# already knows same-dimensions and we want to preserve that — so the
# prompt acknowledges both forms.
#
# MIXED prompt: full prompt with ARC-AGI puzzle framing — the rule
# generalizes across all input/output pairs of a puzzle, encoded one T
# per pair. This is the context the rule-transfer formats
# (multi_pair_to_rule, test_substrate_prediction) need.

SYSTEM_MESSAGE_SAME = """T represents the transformation between INPUT and OUTPUT. Each cell
is an atomic unit colored 0-9.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T."""

SYSTEM_MESSAGE_DIFF = """T represents the transformation between INPUT and OUTPUT. Each cell
is an atomic unit colored 0-9.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T.

T grid legend when INPUT and OUTPUT have different dimensions
(e.g. 3x3 -> 2x4):
T is an aggregate text block with these sections in fixed order,
separated by blank lines:
  SIZE     overall dimensions:  H x W -> h x w  with relation tags
  BG       background color:  in_bg -> out_bg  with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)
Whole-grid statistics — diagnostic only, not lossless. No per-cell
decoder.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0"""

SYSTEM_MESSAGE_MIXED = """ARC-AGI puzzle contains INPUT/OUTPUT grid pairs where each cell is an
atomic unit colored 0-9. There is exactly one transformation rule that
generalizes across all input/output pairs of a puzzle. The rule is
encoded in T grids — one T per pair, and the underlying rule is the
same across all of them.

T grid legend when INPUT and OUTPUT have the same dimensions
(e.g. 3x3 -> 3x3):
  .       cell unchanged
  0-9     cell changed to this output color
Each cell is independent: T[r,c] depends only on INPUT[r,c] and
OUTPUT[r,c], not on neighbors. Lossless — OUTPUT is fully
reconstructible from INPUT + T.

T grid legend when INPUT and OUTPUT have different dimensions
(e.g. 3x3 -> 2x4):
T is an aggregate text block with these sections in fixed order,
separated by blank lines:
  SIZE     overall dimensions:  H x W -> h x w  with relation tags
  BG       background color:  in_bg -> out_bg  with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)
Whole-grid statistics — diagnostic only, not lossless. No per-cell
decoder.

Relation tags for numeric pairs a -> b:
  =        a == b
  ×N       b = a * N, integer N > 1
  ÷N       a = b * N, integer N > 1
  Δ±N      additive offset (b - a)
  new      a == 0 and b > 0
  dropped  a > 0 and b == 0"""

# LIT shares the same prompt content as DIFF (both alphabets, no
# puzzle framing) — LIT trains on both alphabets in single-pair
# literacy form, so the prompt must define both. SAME comes after LIT
# and narrows focus to same-dim only; DIFF re-expands to both alphabets
# to preserve same-dim retention while training diff-dim records.
SYSTEM_MESSAGE_LIT = SYSTEM_MESSAGE_DIFF

SYSTEM_MESSAGE_BY_STAGE = {
    "lit":   SYSTEM_MESSAGE_LIT,
    "same":  SYSTEM_MESSAGE_SAME,
    "diff":  SYSTEM_MESSAGE_DIFF,
    "mixed": SYSTEM_MESSAGE_MIXED,
}


# ---------------------------------------------------------------------------
# Probe set carve-out from train_pool. Same probe puzzles across all three
# stages so we can measure per-stage progression (literacy after `same`,
# diff retention after `diff`, integration after `mixed`).

PROBE_SIZE = 50
PROBE_SEED_MULT = 7919  # arbitrary prime, separate from aug seed streams

# api_eval: held-out set carved from train_pool, distinct from probe.
# Used for API-based inference testing across all phases (Phase 1
# substrate/grid runs, Phase 2 code-pipeline checkpoint selection, etc.).
# Held from training AND from the probe. No JSONL is generated in
# Phase 1 — only the puzzle id list is locked. Phase 2's harness will
# render these puzzles in whatever format Phase 2 needs.
API_EVAL_SIZE = 50
API_EVAL_SEED_MULT = 7841  # different prime from PROBE_SEED_MULT


# ---------------------------------------------------------------------------
# Per-stage config: substrate filter, system prompt key, task mix, augment
# policy, output filenames. Mirrored from the per-stage Axolotl YAML
# configs.

STAGE_CONFIG = {
    "lit": {
        "stage_name": "phase1_lit",
        "stage_key":  "lit",
        "substrate_filter": "both",  # both alphabets, single-pair only
        "seed": 42,
        # Pure literacy: only the single-pair atomic formats. No multi-
        # pair, no test prediction, no direct output. This stage's job
        # is to lock in the substrate alphabet (both same-dim grid and
        # diff-dim aggregate text). Probes after this gate sub-stage
        # progression into SAME.
        "task_mix": {
            "pair_to_substrate":   0.65,
            "substrate_to_output": 0.35,  # intrinsically same-dim only
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1_lit_train.jsonl",
            "probe":    DATA_SFT_DIR / "phase1_lit_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1_lit_manifest.json",
        },
    },
    "same": {
        "stage_name": "phase1_same",
        "stage_key":  "same",        # selects SYSTEM_MESSAGE
        "substrate_filter": "same",  # only emit records whose T target is same-dim
        "seed": 42,
        # All 5 formats trainable. substrate_to_output is intrinsically
        # same-dim. The other 4 are filtered to same-dim pairs at the
        # item-enumeration step.
        "task_mix": {
            "pair_to_substrate":         0.15,
            "substrate_to_output":       0.15,
            "multi_pair_to_rule":        0.25,
            "test_substrate_prediction": 0.35,
            "direct_output_grid":        0.10,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1_same_train.jsonl",
            "probe":    DATA_SFT_DIR / "phase1_same_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1_same_manifest.json",
        },
    },
    "diff": {
        "stage_name": "phase1_diff",
        "stage_key":  "diff",
        "substrate_filter": "diff",
        "seed": 42,
        # substrate_to_output has no decoder for diff-dim, so it is
        # absent from this stage's mix (the eligibility filter drops it
        # automatically; this config is the explicit statement).
        "task_mix": {
            "pair_to_substrate":         0.20,
            "multi_pair_to_rule":        0.30,
            "test_substrate_prediction": 0.40,
            "direct_output_grid":        0.10,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1_diff_train.jsonl",
            "probe":    DATA_SFT_DIR / "phase1_diff_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1_diff_manifest.json",
        },
    },
    "mixed": {
        "stage_name": "phase1_mixed",
        "stage_key":  "mixed",
        "substrate_filter": "both",  # no filter
        "seed": 42,
        # Compensating direct_output_grid up because diff-dim pairs no
        # longer have substrate_to_output to ride on.
        "task_mix": {
            "pair_to_substrate":         0.05,
            "substrate_to_output":       0.05,
            "multi_pair_to_rule":        0.25,
            "test_substrate_prediction": 0.40,
            "direct_output_grid":        0.25,
        },
        "augment": {
            "train": {"d4": True, "color_perms": 3, "pair_subsetting": True,
                      "pair_subset_min": 1, "pair_subset_max": 3},
        },
        "out_files": {
            "train":    DATA_SFT_DIR / "phase1_mixed_train.jsonl",
            "probe":    DATA_SFT_DIR / "phase1_mixed_probe.jsonl",
            "manifest": DATA_SFT_DIR / "phase1_mixed_manifest.json",
        },
    },
}


# Formats that need at least N train pairs (after pair-subsetting).
MIN_TRAIN_PAIRS = {
    "multi_pair_to_rule":        3,
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
    raw = json.loads(path.read_text())
    return {
        "train": [{"input": parse_grid(p["input"]),
                   "output": parse_grid(p["output"])} for p in raw["train"]],
        "test":  [{"input": parse_grid(p["input"]),
                   "output": parse_grid(p["output"])} for p in raw["test"]],
    }


def is_same_size(pair) -> bool:
    inp, out = pair["input"], pair["output"]
    return len(inp) == len(out) and len(inp[0]) == len(out[0])


def pair_substrate_type(pair) -> str:
    return "same" if is_same_size(pair) else "diff"


# ---------------------------------------------------------------------------
# D4 + color permutation + pair subsetting (rule-preserving augmentations)

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
    "transpose":      lambda g: [list(row) for row in zip(*g)],
    "anti_transpose": lambda g: [list(row) for row in zip(*[r[::-1] for r in g[::-1]])],
}


def apply_d4(puzzle, op_name):
    op = D4_OPS[op_name]
    return {
        "train": [{"input": op(p["input"]), "output": op(p["output"])}
                  for p in puzzle["train"]],
        "test":  [{"input": op(p["input"]), "output": op(p["output"])}
                  for p in puzzle["test"]],
    }


def random_color_perm(rng):
    while True:
        p = list(range(10))
        rng.shuffle(p)
        if p != list(range(10)):
            return p


def apply_color_perm(puzzle, perm):
    def m(g):
        return [[perm[c] for c in row] for row in g]
    return {
        "train": [{"input": m(p["input"]), "output": m(p["output"])}
                  for p in puzzle["train"]],
        "test":  [{"input": m(p["input"]), "output": m(p["output"])}
                  for p in puzzle["test"]],
    }


def apply_pair_subset(puzzle, subset_indices):
    return {
        "train": [puzzle["train"][i] for i in subset_indices],
        "test":  list(puzzle["test"]),
    }


def augmentation_variants(puzzle, aug_cfg, rng):
    variants = []
    d4_ops = list(D4_OPS.keys()) if aug_cfg.get("d4") else ["identity"]
    n_color_perms = aug_cfg.get("color_perms", 0)
    color_perms = [(None, list(range(10)))]
    for i in range(n_color_perms):
        color_perms.append((f"cp{i}", random_color_perm(rng)))

    n_train = len(puzzle["train"])
    pair_subsets = [tuple(range(n_train))]
    if aug_cfg.get("pair_subsetting") and n_train >= 2:
        lo = aug_cfg.get("pair_subset_min", 1)
        hi = min(aug_cfg.get("pair_subset_max", n_train), n_train)
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
    s = encode_auto(inp, out)
    return s if isinstance(s, str) else format_grid(s)


# ---------------------------------------------------------------------------
# Format renderers. Each takes explicit pair/test indices — no random
# choice inside the renderer. The generator's item-enumeration step is
# responsible for choosing which pair to target.

def fmt_pair_to_substrate(puzzle, pair_idx):
    pair = puzzle["train"][pair_idx]
    user = (
        f"INPUT:\n{grid_to_str(pair['input'])}\n\n"
        f"OUTPUT:\n{grid_to_str(pair['output'])}\n\n"
        f"T:\n"
    )
    target = render_substrate(pair["input"], pair["output"])
    return user, target


def fmt_substrate_to_output(puzzle, pair_idx):
    pair = puzzle["train"][pair_idx]
    # Caller must ensure same-dim (no decoder for diff-dim).
    if not is_same_size(pair):
        return None
    sub = encode(pair["input"], pair["output"])
    user = (
        f"INPUT:\n{grid_to_str(pair['input'])}\n\n"
        f"T:\n{format_grid(sub)}\n\n"
        f"OUTPUT:\n"
    )
    target = grid_to_str(pair["output"])
    return user, target


def fmt_multi_pair_to_rule(puzzle, trailing_idx):
    if len(puzzle["train"]) < 3:
        return None
    user_lines = []
    for i, pair in enumerate(puzzle["train"]):
        if i == trailing_idx:
            continue
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"T:\n{render_substrate(pair['input'], pair['output'])}")
    trailing = puzzle["train"][trailing_idx]
    user_lines.append(f"INPUT:\n{grid_to_str(trailing['input'])}")
    user_lines.append(f"OUTPUT:\n{grid_to_str(trailing['output'])}")
    user = "\n\n".join(user_lines) + "\n\nT:\n"
    target = render_substrate(trailing["input"], trailing["output"])
    return user, target


def fmt_test_substrate_prediction(puzzle, test_idx):
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for pair in puzzle["train"]:
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
        user_lines.append(f"T:\n{render_substrate(pair['input'], pair['output'])}")
    user_lines.append(f"INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nT:\n"
    target = render_substrate(test_pair["input"], test_pair["output"])
    return user, target


def fmt_direct_output_grid(puzzle, test_idx):
    if len(puzzle["train"]) < 2 or not puzzle["test"]:
        return None
    test_pair = puzzle["test"][test_idx]
    user_lines = []
    for pair in puzzle["train"]:
        user_lines.append(f"INPUT:\n{grid_to_str(pair['input'])}")
        user_lines.append(f"OUTPUT:\n{grid_to_str(pair['output'])}")
    user_lines.append(f"INPUT:\n{grid_to_str(test_pair['input'])}")
    user = "\n\n".join(user_lines) + "\n\nOUTPUT:\n"
    target = grid_to_str(test_pair["output"])
    return user, target


FORMAT_FNS = {
    "pair_to_substrate":         fmt_pair_to_substrate,
    "substrate_to_output":       fmt_substrate_to_output,
    "multi_pair_to_rule":        fmt_multi_pair_to_rule,
    "test_substrate_prediction": fmt_test_substrate_prediction,
    "direct_output_grid":        fmt_direct_output_grid,
}


# ---------------------------------------------------------------------------
# Item enumeration: one item per (variant, format, target-pair-index).
# Each item carries its substrate_type so the stage's filter can keep or
# drop it.

def enumerate_items_for_variant(variant_puzzle, prov_aug, rep_pid, sources,
                                task_mix):
    items = []
    n_train = len(variant_puzzle["train"])
    n_test  = len(variant_puzzle["test"])

    base = {
        "cluster_rep_pid": rep_pid,
        "cluster_sources": sources,
        "variant_puzzle":  variant_puzzle,
        "prov_aug":        prov_aug,
    }

    # pair_to_substrate: one item per train pair
    if task_mix.get("pair_to_substrate", 0) > 0:
        for i in range(n_train):
            stype = pair_substrate_type(variant_puzzle["train"][i])
            items.append({**base, "format": "pair_to_substrate",
                          "pair_idx": i, "substrate_type": stype})

    # substrate_to_output: only same-dim train pairs (decoder exists)
    if task_mix.get("substrate_to_output", 0) > 0:
        for i in range(n_train):
            if is_same_size(variant_puzzle["train"][i]):
                items.append({**base, "format": "substrate_to_output",
                              "pair_idx": i, "substrate_type": "same"})

    # multi_pair_to_rule: one item per trailing position
    if (task_mix.get("multi_pair_to_rule", 0) > 0
            and n_train >= MIN_TRAIN_PAIRS["multi_pair_to_rule"]):
        for t_idx in range(n_train):
            stype = pair_substrate_type(variant_puzzle["train"][t_idx])
            items.append({**base, "format": "multi_pair_to_rule",
                          "trailing_idx": t_idx, "substrate_type": stype})

    # test_substrate_prediction + direct_output_grid: one item per test pair
    if n_train >= 2 and n_test > 0:
        for test_idx in range(n_test):
            stype = pair_substrate_type(variant_puzzle["test"][test_idx])
            if task_mix.get("test_substrate_prediction", 0) > 0:
                items.append({**base, "format": "test_substrate_prediction",
                              "test_idx": test_idx, "substrate_type": stype})
            if task_mix.get("direct_output_grid", 0) > 0:
                items.append({**base, "format": "direct_output_grid",
                              "test_idx": test_idx, "substrate_type": stype})

    return items


# ---------------------------------------------------------------------------
# Record assembly

def make_record(item, stage_cfg, bucket):
    fn = FORMAT_FNS[item["format"]]
    if item["format"] == "multi_pair_to_rule":
        out = fn(item["variant_puzzle"], item["trailing_idx"])
    elif item["format"] in ("pair_to_substrate", "substrate_to_output"):
        out = fn(item["variant_puzzle"], item["pair_idx"])
    else:  # test_substrate_prediction, direct_output_grid
        out = fn(item["variant_puzzle"], item["test_idx"])

    if out is None:
        return None
    user, target = out

    prov = {
        "format":         item["format"],
        "stage":          stage_cfg["stage_name"],
        "stage_key":      stage_cfg["stage_key"],
        "bucket":         bucket,
        "puzzle_id":      item["cluster_rep_pid"],
        "sources":        item["cluster_sources"],
        "substrate_type": item["substrate_type"],
        **item["prov_aug"],
    }
    if "pair_idx" in item:
        prov["pair_index"] = item["pair_idx"]
    if "trailing_idx" in item:
        prov["trailing_pair_index"] = item["trailing_idx"]
    if "test_idx" in item:
        prov["test_pair_index"] = item["test_idx"]

    return {
        "messages": [
            {"role": "system",
             "content": SYSTEM_MESSAGE_BY_STAGE[stage_cfg["stage_key"]]},
            {"role": "user",      "content": user},
            {"role": "assistant", "content": target},
        ],
        "provenance": prov,
    }


# ---------------------------------------------------------------------------
# Generation loop

def augmentation_rank(prov: dict) -> int:
    """Difficulty rank: 0 identity / 1 color / 2 D4 / 3 D4+color.
    Used for curriculum sort within the train file."""
    has_d4 = prov.get("d4_op", "identity") != "identity"
    has_color = prov.get("color_perm_seed") is not None
    return (2 if has_d4 else 0) + (1 if has_color else 0)


def generate_for_bucket(bucket_name, cluster_list, aug_cfg, stage_cfg,
                        master_seed, max_per_puzzle):
    """For each cluster in the bucket: expand augmentations, enumerate
    per-(variant, format, target-pair) items, filter by substrate_type,
    then sample per-format to hit the mix targets exactly."""
    items = []
    skip_counter = Counter()
    substrate_filter = stage_cfg["substrate_filter"]
    task_mix = stage_cfg["task_mix"]

    base_variant_count = 0

    for cluster in cluster_list:
        rep_pid = cluster["rep_pid"]
        sources = cluster["sources"]
        path = PUZZLES_DIR / cluster["files"][0]
        if not path.exists():
            skip_counter["file_missing"] += 1
            continue
        puzzle = load_puzzle(path)

        per_puzzle_seed = (master_seed * 1000003
                           + sum(ord(c) for c in rep_pid)) & 0x7FFFFFFF
        rng = random.Random(per_puzzle_seed)

        variants = augmentation_variants(puzzle, aug_cfg, rng)
        if len(variants) > max_per_puzzle:
            variants = rng.sample(variants, max_per_puzzle)

        for variant_puzzle, prov_aug in variants:
            v_items = enumerate_items_for_variant(
                variant_puzzle, prov_aug, rep_pid, sources, task_mix
            )
            if substrate_filter != "both":
                v_items = [it for it in v_items
                           if it["substrate_type"] == substrate_filter]
            if v_items:
                base_variant_count += 1
                items.extend(v_items)

    # Per-format target sampling. Target is ratio × base_variant_count,
    # so the final dataset is the size of the (variant, post-filter)
    # population, with formats in their declared ratios.
    format_targets = {
        fmt: int(round(ratio * base_variant_count))
        for fmt, ratio in task_mix.items()
    }
    pool_sizes = Counter()
    for it in items:
        pool_sizes[it["format"]] += 1

    records = []
    fmt_counter = Counter()
    rng_pick = random.Random(master_seed + 99)

    for fmt, target in format_targets.items():
        pool = [it for it in items if it["format"] == fmt]
        if len(pool) < target:
            skip_counter[f"{fmt}_pool_short_by"] = target - len(pool)
            chosen = pool
        else:
            chosen = rng_pick.sample(pool, target)
        for it in chosen:
            rec = make_record(it, stage_cfg, bucket=bucket_name)
            if rec is None:
                skip_counter[f"{fmt}_returned_none"] += 1
                continue
            records.append(rec)
            fmt_counter[fmt] += 1

    skip_counter["_pool_sizes"] = dict(pool_sizes)
    skip_counter["_variant_count"] = base_variant_count
    return records, fmt_counter, skip_counter


# ---------------------------------------------------------------------------
# Probe set: identity augmentation, one record per (cluster, format,
# target-pair). Same seed across stages so probe puzzle ids are shared.

def select_held_out_clusters(train_pool, seed):
    """Select probe and api_eval clusters from train_pool, guaranteed
    non-overlapping. Returns (probe_clusters, api_eval_clusters).

    The probe is sampled first, then api_eval is sampled from the
    remaining pool (probe-excluded). This way probe ids are stable
    even if API_EVAL_SIZE / seed change later.
    """
    sorted_pool = sorted(train_pool, key=lambda c: c["rep_pid"])
    if PROBE_SIZE + API_EVAL_SIZE > len(sorted_pool):
        raise ValueError(f"train_pool too small ({len(sorted_pool)} < "
                         f"{PROBE_SIZE + API_EVAL_SIZE})")
    rng_probe = random.Random(seed * PROBE_SEED_MULT)
    probe_clusters = rng_probe.sample(sorted_pool, PROBE_SIZE)
    probe_ids = {c["rep_pid"] for c in probe_clusters}

    remaining = [c for c in sorted_pool if c["rep_pid"] not in probe_ids]
    rng_api = random.Random(seed * API_EVAL_SEED_MULT)
    api_eval_clusters = rng_api.sample(remaining, API_EVAL_SIZE)
    return probe_clusters, api_eval_clusters


def generate_probe_records(probe_clusters, stage_cfg, master_seed):
    """One record per (cluster, eligible format, eligible-target-pair),
    using identity augmentation. Stage filter applied — diff probe only
    covers diff pairs, etc."""
    records = []
    fmt_counter = Counter()
    skip_counter = Counter()
    substrate_filter = stage_cfg["substrate_filter"]
    task_mix = stage_cfg["task_mix"]

    for cluster in probe_clusters:
        rep_pid = cluster["rep_pid"]
        sources = cluster["sources"]
        path = PUZZLES_DIR / cluster["files"][0]
        if not path.exists():
            skip_counter["file_missing"] += 1
            continue
        puzzle = load_puzzle(path)
        prov_aug = {
            "d4_op": "identity",
            "color_perm_seed": None,
            "pair_subset": list(range(len(puzzle["train"]))),
        }
        v_items = enumerate_items_for_variant(
            puzzle, prov_aug, rep_pid, sources, task_mix
        )
        if substrate_filter != "both":
            v_items = [it for it in v_items
                       if it["substrate_type"] == substrate_filter]
        # For multi_pair_to_rule keep only trailing_idx=0 per cluster
        # (one probe per puzzle is sufficient; rotation coverage is a
        # training concern, not an evaluation concern).
        seen_mp = set()
        for it in v_items:
            if it["format"] == "multi_pair_to_rule":
                key = (rep_pid, it["substrate_type"])
                if key in seen_mp:
                    continue
                if it.get("trailing_idx", 0) != 0:
                    continue
                seen_mp.add(key)
            rec = make_record(it, stage_cfg, bucket="probe")
            if rec is None:
                skip_counter[f"{it['format']}_returned_none"] += 1
                continue
            records.append(rec)
            fmt_counter[it["format"]] += 1
    return records, fmt_counter, skip_counter


# ---------------------------------------------------------------------------
# Main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["lit", "same", "diff", "mixed"], required=True)
    ap.add_argument("--sample-only", action="store_true",
                    help="Generate ~50 examples per bucket for review.")
    ap.add_argument("--max-per-puzzle", type=int, default=24,
                    help="Cap augmented variants per puzzle. Default 24.")
    ap.add_argument("--curriculum", choices=["sort", "shuffle"], default="sort",
                    help="train.jsonl ordering. 'sort' (default) orders by "
                         "augmentation difficulty rank.")
    args = ap.parse_args()

    cfg = STAGE_CONFIG[args.stage]
    splits = json.loads(SPLITS_FILE.read_text())
    seed = cfg["seed"]

    DATA_SFT_DIR.mkdir(exist_ok=True)
    PROBE_IDS_FILE.parent.mkdir(exist_ok=True)

    probe_clusters, api_eval_clusters = select_held_out_clusters(
        splits["buckets"]["train_pool"], seed
    )
    probe_pids = {c["rep_pid"] for c in probe_clusters}
    api_eval_pids = {c["rep_pid"] for c in api_eval_clusters}

    # Stable id files. Mismatch on re-run = seed drift; refuse to
    # silently overwrite.
    def _write_or_verify_ids(path, pids):
        expected = sorted(pids)
        if path.exists():
            existing = sorted(path.read_text().strip().split("\n"))
            if existing != expected:
                print(f"ERROR: ids drifted from {path}", file=sys.stderr)
                sys.exit(4)
        else:
            path.write_text("\n".join(expected) + "\n")
            print(f"Wrote {path.relative_to(REPO)} ({len(expected)} ids)")

    _write_or_verify_ids(PROBE_IDS_FILE, probe_pids)
    _write_or_verify_ids(API_EVAL_IDS_FILE, api_eval_pids)

    # Held-out from Phase 1 training:
    #   probe-50 (between-stage gate, also rendered as probe.jsonl)
    #   api_eval-50 (locked ids only; rendered later by Phase 2)
    #   a2e_dev_hard-30 (sacred for Phase 2/3 checkpoint selection)
    #   a2e_final_hard-34 (sacred end-of-run; physically isolated)
    train_pool_minus_holdouts = [
        c for c in splits["buckets"]["train_pool"]
        if c["rep_pid"] not in probe_pids
        and c["rep_pid"] not in api_eval_pids
    ]
    train_clusters = (
        train_pool_minus_holdouts
        + splits["buckets"]["a2e_train_hard"]
        + splits["buckets"]["a2e_leakers"]
    )

    if args.sample_only:
        rng = random.Random(seed)
        train_clusters = rng.sample(train_clusters, min(20, len(train_clusters)))
        args.max_per_puzzle = 3

    print(f"Stage: {cfg['stage_name']}  filter={cfg['substrate_filter']}  "
          f"seed={seed}  max_per_puzzle={args.max_per_puzzle}")
    print(f"Train clusters: {len(train_clusters)} "
          f"(train_pool {len(train_pool_minus_holdouts)} - holdouts already removed)")
    print(f"Probe clusters: {len(probe_clusters)} (between-stage gate)")
    print(f"API-eval clusters: {len(api_eval_clusters)} "
          f"(locked, not generated as JSONL in Phase 1)")

    print("\nGenerating train…")
    train_records, train_fmt, train_skip = generate_for_bucket(
        "train", train_clusters, cfg["augment"]["train"], cfg,
        master_seed=seed, max_per_puzzle=args.max_per_puzzle,
    )
    print(f"  {len(train_records)} records")
    for fmt, n in sorted(train_fmt.items()):
        pct = 100 * n / len(train_records) if train_records else 0
        print(f"    {fmt}: {n} ({pct:.1f}%)")
    if train_skip:
        print(f"  skips: {dict(train_skip)}")

    print("\nGenerating probe…")
    probe_records, probe_fmt, probe_skip = generate_probe_records(
        probe_clusters, cfg, master_seed=seed,
    )
    print(f"  {len(probe_records)} records")
    for fmt, n in sorted(probe_fmt.items()):
        print(f"    {fmt}: {n}")
    if probe_skip:
        print(f"  skips: {dict(probe_skip)}")

    # Curriculum sort the train file. Two-level order:
    #   1. substrate_type: same first, then diff
    #   2. within each substrate_type: augmentation rank 0 → 3
    # For SAME / DIFF stages (single substrate type) this collapses to
    # rank-only order. For LIT and MIXED, this imposes the same-before-
    # diff sub-curriculum — model sees the simpler pixel grid alphabet
    # locked down before the diff-size aggregate text block alphabet.
    rng_shuf = random.Random(seed + 2)
    if args.curriculum == "sort":
        by_key = defaultdict(list)
        for r in train_records:
            sub_type = r["provenance"]["substrate_type"]
            rank = augmentation_rank(r["provenance"])
            by_key[(sub_type, rank)].append(r)
        train_records = []
        for sub_type in ("same", "diff"):
            for rank in (0, 1, 2, 3):
                bucket = by_key.get((sub_type, rank), [])
                rng_shuf.shuffle(bucket)
                train_records.extend(bucket)
        rank_counts = {
            f"{sub_type}_{rank}": len(by_key.get((sub_type, rank), []))
            for sub_type in ("same", "diff")
            for rank in (0, 1, 2, 3)
        }
    else:
        rng_shuf.shuffle(train_records)
        rank_counts = None

    out_train = cfg["out_files"]["train"]
    out_probe = cfg["out_files"]["probe"]
    out_manifest = cfg["out_files"]["manifest"]
    if args.sample_only:
        out_train = out_train.with_name(out_train.stem + "_sample.jsonl")
        out_probe = out_probe.with_name(out_probe.stem + "_sample.jsonl")
        out_manifest = out_manifest.with_name(out_manifest.stem + "_sample.json")

    with out_train.open("w") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out_probe.open("w") as f:
        for r in probe_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "stage": cfg["stage_name"],
        "stage_key": cfg["stage_key"],
        "substrate_filter": cfg["substrate_filter"],
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
        "probe": {
            "file": str(out_probe.relative_to(REPO)),
            "n_records": len(probe_records),
            "n_clusters": len(probe_clusters),
            "format_counts": dict(probe_fmt),
            "skipped": dict(probe_skip),
            "ids_file": str(PROBE_IDS_FILE.relative_to(REPO)),
        },
        "held_out_locked": {
            "phase1_probe_size": len(probe_clusters),
            "phase1_probe_ids_file": str(PROBE_IDS_FILE.relative_to(REPO)),
            "api_eval_size": len(api_eval_clusters),
            "api_eval_ids_file": str(API_EVAL_IDS_FILE.relative_to(REPO)),
            "a2e_dev_hard_size": len(splits["buckets"]["a2e_dev_hard"]),
            "a2e_dev_hard_use": "reserved for Phase 2/3 code-pipeline checkpoint selection; not touched in Phase 1",
            "a2e_final_hard_size": len(splits["buckets"]["a2e_final_hard"]),
            "a2e_final_hard_use": "sacred end-of-run headline; physically isolated in puzzles_frozen/",
        },
        "in_flight_eval": {
            "policy": "Axolotl val_set_size carve from train (loss-only monitor, not a checkpoint-selection authority, not a generalization metric). The only real Phase 1 gate is phase1_probe exact-match scoring.",
        },
    }
    out_manifest.write_text(json.dumps(manifest, indent=2))

    print(f"\nWrote:")
    print(f"  {out_train.relative_to(REPO)}")
    print(f"  {out_probe.relative_to(REPO)}")
    print(f"  {out_manifest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
