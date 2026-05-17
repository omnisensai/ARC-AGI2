"""Generate Phase 1 substrate training data.

Reads same-size puzzles from data/arc1_train, data/arc1_eval, data/arc2_train.
Excludes the 10 locked baseline_10 puzzles. Filters to puzzles where every
(input, output) pair preserves grid dimensions.

For each (input, output) pair, applies augmentations and emits two training
records:
  Phase 1a:  (input, output) -> substrate
  Phase 1b:  (input, substrate) -> output

Augmentations:
  - D4 (8 variants: rotate 0/90/180/270, optionally flipped)
  - Color permutations (random permutations of {0..9} applied to all cells)

Output:
  phase1_train.jsonl      ~99% of puzzles after held-out split
  phase1_dev.jsonl        100 puzzles, never seen in training, used to monitor
                          encode/decode accuracy during fine-tuning

Usage:
  python3 gen_phase1_data.py                       # defaults: D4 only, no color perms
  python3 gen_phase1_data.py --color-perms 5       # 5 random color perms per (pair, rotation)
  python3 gen_phase1_data.py --no-augment          # raw only (no D4, no color perms)
  python3 gen_phase1_data.py --dev-size 100        # change dev puzzle count
"""
import argparse
import json
import random
from itertools import product
from pathlib import Path

from substrate import background_of, encode, decode, is_same_size, format_grid


PHASE1A_SYSTEM = (
    "You compute ARC transformation substrates. Given an input grid and an output "
    "grid (both same size), produce the substrate that describes the per-cell "
    "transformation. Substrate alphabet: '.' (background cell unchanged), '=' "
    "(non-background cell preserved), <digit> (cell changed to this color). "
    "Background = most common color in the input. Substrate has identical dimensions."
)

PHASE1B_SYSTEM = (
    "You apply ARC transformation substrates. Given an input grid and a substrate, "
    "produce the output grid. Substrate alphabet: '.' (output equals background), "
    "'=' (output equals input cell), <digit> (output is this color). Background = "
    "most common color in the input. Output has identical dimensions."
)


def rotate90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def flip_h(grid):
    return [row[::-1] for row in grid]


def d4_variants(grid):
    """Return all 8 D4 transforms of a grid, in a fixed order."""
    out = []
    g = grid
    for _ in range(4):
        out.append(g)
        g = rotate90(g)
    g = flip_h(grid)
    for _ in range(4):
        out.append(g)
        g = rotate90(g)
    return out


def apply_color_perm(grid, perm):
    """perm: list of 10 ints mapping old color -> new color."""
    return [[perm[c] if isinstance(c, int) else c for c in row] for row in grid]


def make_record_1a(inp, out, bg, puzzle_id, aug_tag):
    """Phase 1a: (input, output) -> substrate."""
    sub = encode(inp, out, bg)
    return {
        "task": "phase1a",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "messages": [
            {"role": "system", "content": PHASE1A_SYSTEM},
            {"role": "user", "content": f"INPUT:\n{format_grid(inp)}\n\nOUTPUT:\n{format_grid(out)}"},
            {"role": "assistant", "content": format_grid(sub)},
        ],
    }


def make_record_1b(inp, out, bg, puzzle_id, aug_tag):
    """Phase 1b: (input, substrate) -> output."""
    sub = encode(inp, out, bg)
    return {
        "task": "phase1b",
        "puzzle_id": puzzle_id,
        "aug": aug_tag,
        "messages": [
            {"role": "system", "content": PHASE1B_SYSTEM},
            {"role": "user", "content": f"INPUT:\n{format_grid(inp)}\n\nSUBSTRATE:\n{format_grid(sub)}"},
            {"role": "assistant", "content": format_grid(out)},
        ],
    }


def gen_pair_records(inp, out, puzzle_id, n_color_perms, no_augment, rng):
    """Yield records for one (input, output) pair, across augmentations."""
    if no_augment:
        d4_inputs, d4_outputs = [inp], [out]
        d4_tags = ["d4_0"]
    else:
        d4_inputs = d4_variants(inp)
        d4_outputs = d4_variants(out)
        d4_tags = [f"d4_{i}" for i in range(8)]

    for d4_idx, (i_d4, o_d4, tag) in enumerate(zip(d4_inputs, d4_outputs, d4_tags)):
        bg = background_of(i_d4)
        yield make_record_1a(i_d4, o_d4, bg, puzzle_id, tag)
        yield make_record_1b(i_d4, o_d4, bg, puzzle_id, tag)

        for k in range(n_color_perms):
            perm = list(range(10))
            rng.shuffle(perm)
            i_perm = apply_color_perm(i_d4, perm)
            o_perm = apply_color_perm(o_d4, perm)
            bg_perm = background_of(i_perm)
            aug_tag = f"{tag}_cp{k}"
            yield make_record_1a(i_perm, o_perm, bg_perm, puzzle_id, aug_tag)
            yield make_record_1b(i_perm, o_perm, bg_perm, puzzle_id, aug_tag)


def collect_universe(repo_root: Path, locked_eval: set):
    """Return [(puzzle_id, source, path), ...] for all same-size puzzles, excluding locked.

    Shared puzzle IDs across arc1/arc2 have DIFFERENT content (ARC-AGI-2 revised
    many ARC-AGI-1 puzzles). We include both as separate examples — same task ID,
    distinct content. Train/dev split groups by puzzle_id so variants stay together.
    """
    sources = [
        ("arc1_train", repo_root / "data" / "arc1_train"),
        ("arc1_eval",  repo_root / "data" / "arc1_eval"),
        ("arc2_train", repo_root / "data" / "arc2_train"),
    ]
    universe = []
    for src_name, src_dir in sources:
        for path in sorted(src_dir.glob("*.json")):
            pid = path.stem
            if pid in locked_eval:
                continue
            puzzle = json.loads(path.read_text())
            if is_same_size(puzzle):
                universe.append((pid, src_name, path))
    return universe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--color-perms", type=int, default=0,
                    help="random color permutations per (pair, D4 rotation). 0 = D4 only.")
    ap.add_argument("--no-augment", action="store_true",
                    help="raw only, no D4 and no color perms.")
    ap.add_argument("--dev-size", type=int, default=100,
                    help="puzzles held out for phase1_dev.jsonl.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    repo_root = Path(__file__).parent
    splits_dir = repo_root / "splits"
    splits_dir.mkdir(exist_ok=True)

    # Locked eval puzzles (final benchmark, never train on these)
    locked_eval = set(json.loads((splits_dir / "baseline_10.json").read_text())["puzzle_ids"])

    universe = collect_universe(repo_root, locked_eval)
    unique_ids = sorted({pid for pid, _, _ in universe})
    print(f"Universe: {len(universe)} same-size puzzle examples "
          f"({len(unique_ids)} unique IDs across arc1_train + arc1_eval + arc2_train)")

    # Deterministic train/dev split BY puzzle_id (all source variants of an ID
    # go to the same side, preventing arc1/arc2 cross-variant leakage)
    rng = random.Random(args.seed)
    shuffled = list(unique_ids)
    rng.shuffle(shuffled)
    dev_ids = set(shuffled[:args.dev_size])
    train_ids = set(shuffled[args.dev_size:])
    train_examples = sum(1 for pid, _, _ in universe if pid in train_ids)
    dev_examples = sum(1 for pid, _, _ in universe if pid in dev_ids)
    print(f"  train: {len(train_ids)} unique IDs ({train_examples} examples)")
    print(f"  dev:   {len(dev_ids)} unique IDs ({dev_examples} examples)")

    # Save the universe + split manifest (so it's reproducible)
    (splits_dir / "training_universe.json").write_text(json.dumps({
        "description": "Phase 1 training universe: all same-size puzzles from "
                       "ARC-AGI-1 train + eval + ARC-AGI-2 train, minus the 10 "
                       "locked baseline_10 puzzles. Train/dev split by unique "
                       "puzzle_id (variants across sources stay together), seed=42.",
        "seed": args.seed,
        "unique_ids_total": len(unique_ids),
        "examples_total": len(universe),
        "train_unique_ids": len(train_ids),
        "dev_unique_ids": len(dev_ids),
        "train_examples": train_examples,
        "dev_examples": dev_examples,
        "train_ids": sorted(train_ids),
        "dev_ids": sorted(dev_ids),
    }, indent=2))

    train_path = Path(args.out_dir) / "phase1_train.jsonl"
    dev_path = Path(args.out_dir) / "phase1_dev.jsonl"

    rec_rng = random.Random(args.seed + 1)

    n_train = 0
    n_dev = 0
    with open(train_path, "w") as ft, open(dev_path, "w") as fd:
        for pid, src, path in universe:
            puzzle = json.loads(path.read_text())
            sink = ft if pid in train_ids else fd
            for pair_idx, pair in enumerate(puzzle["train"] + puzzle["test"]):
                inp, out = pair["input"], pair["output"]
                for rec in gen_pair_records(inp, out, pid,
                                            args.color_perms, args.no_augment, rec_rng):
                    sink.write(json.dumps(rec) + "\n")
                    if pid in train_ids:
                        n_train += 1
                    else:
                        n_dev += 1

    print(f"\nWrote:")
    print(f"  {train_path}  {n_train:>7,} records")
    print(f"  {dev_path}    {n_dev:>7,} records")
    print(f"  {splits_dir / 'training_universe.json'}")


if __name__ == "__main__":
    main()
