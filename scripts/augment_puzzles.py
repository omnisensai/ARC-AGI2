"""Generate rule-preserving augmentations of ARC puzzles for held-out eval.

Each augmentation = D4 op + color permutation (keeping 0 fixed).
Both preserve the underlying transformation rule. Outputs new puzzle JSONs
that look different on the surface but encode the same logic.

Used to build an internal held-out eval set without burning arc2_eval.

ID scheme — self-describing so you can trace back without opening the manifest:

    {original_pid}_{d4_code}{color_seed:02d}

    d4 code (single char):
      i = identity (no rotation/flip)
      1 = rot 90 deg clockwise
      2 = rot 180
      3 = rot 270
      h = flip horizontal (left/right)
      v = flip vertical   (up/down)
      t = transpose (main diagonal)
      a = anti-transpose (anti-diagonal)

    color_seed (2 digits, 00-99):
      Index of the color permutation. Combined with the global --seed,
      deterministically picks a bijection on {1..9}, keeping 0 fixed.

Example: `009d5c81_t03` = puzzle 009d5c81, transposed, color-perm variant #3.

A manifest.json is also written with the full d4_op name and color_map
for every augmented pid, in case you need the exact mapping.

Usage:
    python3 scripts/augment_puzzles.py \
        --split splits/all_samesize.json \
        --out-dir data/augmented_eval \
        --out-split splits/holdout_augmented_smoke.json \
        --num-puzzles 10 \
        --augs-per-puzzle 1 \
        --seed 42
"""
import argparse
import json
import random
from pathlib import Path


D4_OPS = ["identity", "rot90", "rot180", "rot270",
          "flip_h", "flip_v", "transpose", "anti_transpose"]

D4_CODE = {
    "identity":       "i",
    "rot90":          "1",
    "rot180":         "2",
    "rot270":         "3",
    "flip_h":         "h",
    "flip_v":         "v",
    "transpose":      "t",
    "anti_transpose": "a",
}


def d4_apply(grid, op):
    g = [row[:] for row in grid]
    if op == "identity":
        return g
    if op == "rot90":
        return [list(row) for row in zip(*g[::-1])]
    if op == "rot180":
        return [row[::-1] for row in g[::-1]]
    if op == "rot270":
        return [list(row) for row in zip(*g)][::-1]
    if op == "flip_h":
        return [row[::-1] for row in g]
    if op == "flip_v":
        return g[::-1]
    if op == "transpose":
        return [list(row) for row in zip(*g)]
    if op == "anti_transpose":
        return [list(row)[::-1] for row in zip(*g)][::-1]
    raise ValueError(f"unknown d4 op {op}")


def color_perm_from_seed(global_seed: int, color_idx: int) -> dict:
    """Deterministic color permutation from (global_seed, color_idx).

    Same inputs → same permutation, every time. Enables reproducible
    pid labels like '..._t03' that always refer to the same augmentation.
    """
    rng = random.Random(f"{global_seed}-{color_idx}")
    perm = list(range(1, 10))
    rng.shuffle(perm)
    return {0: 0, **{i: c for i, c in enumerate(perm, start=1)}}


def apply_color(grid, mapping):
    return [[mapping[c] for c in row] for row in grid]


def augment_puzzle(puzzle, d4_op, color_map):
    def transform(g):
        return apply_color(d4_apply(g, d4_op), color_map)
    return {
        "train": [{"input": transform(p["input"]), "output": transform(p["output"])}
                  for p in puzzle["train"]],
        "test": [{"input": transform(p["input"]), "output": transform(p["output"])}
                 for p in puzzle["test"]],
    }


def find_puzzle_file(pid):
    """Search the non-eval puzzle dirs. arc2_eval is held out and NOT searched."""
    for d in ["data/arc1_train", "data/arc1_eval", "data/arc2_train"]:
        p = Path(d) / f"{pid}.json"
        if p.exists():
            return p
    raise FileNotFoundError(f"puzzle {pid} not found in non-eval dirs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--out-dir", default="data/augmented_eval")
    ap.add_argument("--out-split", required=True)
    ap.add_argument("--num-puzzles", type=int, default=10)
    ap.add_argument("--augs-per-puzzle", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    selection_rng = random.Random(args.seed)
    raw = json.loads(Path(args.split).read_text())
    if isinstance(raw, dict):
        # Try common key names; fall back to first list-valued entry
        base_pids = raw.get("puzzle_ids") or raw.get("pids")
        if base_pids is None:
            base_pids = next(v for v in raw.values() if isinstance(v, list))
    else:
        base_pids = raw

    sample = selection_rng.sample(base_pids, min(args.num_puzzles, len(base_pids)))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    new_pids = []
    manifest = []
    aug_rng = random.Random(args.seed + 1)  # separate from sample selection
    for pid in sample:
        src = find_puzzle_file(pid)
        puzzle = json.loads(src.read_text())
        for k in range(args.augs_per_puzzle):
            d4_op = aug_rng.choice(D4_OPS)
            color_idx = aug_rng.randrange(100)  # 0-99 fits in 2 digits
            color_map = color_perm_from_seed(args.seed, color_idx)
            aug = augment_puzzle(puzzle, d4_op, color_map)

            new_pid = f"{pid}_{D4_CODE[d4_op]}{color_idx:02d}"
            (out_dir / f"{new_pid}.json").write_text(json.dumps(aug))
            new_pids.append(new_pid)
            manifest.append({
                "augmented_pid": new_pid,
                "source_pid": pid,
                "d4_op": d4_op,
                "d4_code": D4_CODE[d4_op],
                "color_seed": color_idx,
                "color_map": color_map,
            })

    Path(args.out_split).write_text(json.dumps(new_pids, indent=2) + "\n")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"Wrote {len(new_pids)} augmented puzzles to {out_dir}/")
    print(f"Wrote split file: {args.out_split}")
    print(f"Wrote manifest: {out_dir}/manifest.json")
    print()
    print("Sample augmentations (id decodes as: source_d4code colorseed):")
    for m in manifest[:10]:
        active = {k: v for k, v in m["color_map"].items() if k != v}
        print(f"  {m['augmented_pid']:24s} "
              f"<- source={m['source_pid']}, d4={m['d4_op']:14s}, "
              f"non-identity colors={active}")


if __name__ == "__main__":
    main()
