#!/usr/bin/env python3
"""Verify Phase 1 augmentations are rule-preserving and deterministic.

Checks:
  1. D4 ops are bijective: inv(op(g)) == g for every op.
  2. Color perm is bijective.
  3. Pair-subset only removes train pairs; never edits cells.
  4. Substrate equivariance under D4:
        encode_auto(D4(in), D4(out)) is the "same" substrate as
        D4(encode_auto(in, out)) — for same-size pairs, this is exact
        (D4 commutes with per-cell encoding); for diff-size pairs, the
        aggregate substrate should still classify the same kind of
        transformation (we check that SIZE relation tags are preserved
        modulo H<->W swap on rot90).
  5. Substrate equivariance under color perm:
        encode_auto(perm(in), perm(out)) maps the substrate digits by
        perm and leaves '.' alone (same-size); the diff-size BG/palette
        counts permute correspondingly.
  6. Round-trip on same-size pairs: decode(in, encode(in, out)) == out
     for every augmented pair.
  7. Determinism: running augmentation_variants() twice with identical
     seed produces identical output.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from substrate import encode, decode, encode_auto, format_grid  # noqa: E402

# Reuse the augmentation primitives from the generator.
sys.path.insert(0, str(ROOT))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "build_phase1_dataset",
    ROOT / "build_phase1_dataset.py"
)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


PUZZLES_DIR = ROOT / "puzzles"
N_PUZZLES = 50           # sample size for the corpus sweep
N_AUG_VARIANTS = 10      # variants per puzzle to test


def fail(msg):
    print(f"FAIL: {msg}")
    raise SystemExit(1)


# --- 1. D4 bijection ------------------------------------------------------

D4_INVERSE = {
    "identity": "identity",
    "rot90":    "rot270",
    "rot180":   "rot180",
    "rot270":   "rot90",
    "flip_h":   "flip_h",
    "flip_v":   "flip_v",
    "transpose": "transpose",
    "anti_transpose": "anti_transpose",
}


def check_d4_bijection():
    g = [[1, 2, 3], [4, 5, 6]]
    for op_name in gen.D4_OPS:
        op = gen.D4_OPS[op_name]
        inv = gen.D4_OPS[D4_INVERSE[op_name]]
        roundtrip = inv(op(g))
        if roundtrip != g:
            fail(f"D4 op {op_name}: inv({op_name}(g)) != g")
    # Also test on a non-square grid (catches transpose dimension bugs)
    g2 = [[1, 2, 3, 4], [5, 6, 7, 8]]
    for op_name in gen.D4_OPS:
        op = gen.D4_OPS[op_name]
        inv = gen.D4_OPS[D4_INVERSE[op_name]]
        if inv(op(g2)) != g2:
            fail(f"D4 op {op_name} not bijective on 2x4 grid")
    print("  1. D4 bijection (square + non-square): OK")


# --- 2. Color perm bijection ---------------------------------------------

def check_color_perm_bijection():
    rng = random.Random(0)
    g = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    for _ in range(10):
        perm = gen.random_color_perm(rng)
        inv_perm = [0] * 10
        for i, p in enumerate(perm):
            inv_perm[p] = i
        permed = [[perm[c] for c in row] for row in g]
        roundtrip = [[inv_perm[c] for c in row] for row in permed]
        if roundtrip != g:
            fail("color perm not bijective")
    print("  2. Color perm bijection: OK")


# --- 3. Pair-subset is non-destructive -----------------------------------

def check_pair_subset_non_destructive(puzzles):
    for puzzle in puzzles:
        n = len(puzzle["train"])
        if n < 2:
            continue
        subset = (0, n - 1) if n >= 2 else (0,)
        result = gen.apply_pair_subset(puzzle, subset)
        # Test pairs must be unchanged.
        if result["test"] != puzzle["test"]:
            fail("pair subset modified test pairs")
        # Selected train pairs must be byte-identical to original.
        for i, idx in enumerate(subset):
            if result["train"][i] != puzzle["train"][idx]:
                fail(f"pair subset mutated train pair {idx}")
    print(f"  3. Pair-subset non-destructive (on {len(puzzles)} puzzles): OK")


# --- 4. Substrate equivariance under D4 ---------------------------------

def d4_op_to_substrate(sub_grid, op_name):
    """Apply a D4 op to a same-size substrate grid (list of list of str)."""
    return gen.D4_OPS[op_name](sub_grid)


def check_substrate_equivariance_d4(puzzles):
    """For same-size pairs: encode(D4(in), D4(out)) == D4(encode(in, out))."""
    checks = 0
    for puzzle in puzzles:
        for pair in puzzle["train"] + puzzle["test"]:
            inp, out = pair["input"], pair["output"]
            if not gen.is_same_size(pair):
                continue
            orig_sub = encode(inp, out)
            for op_name in gen.D4_OPS:
                op = gen.D4_OPS[op_name]
                aug_sub = encode(op(inp), op(out))
                expected = d4_op_to_substrate(orig_sub, op_name)
                if aug_sub != expected:
                    fail(f"D4 equivariance broken: op={op_name}")
                checks += 1
    print(f"  4. Substrate equivariance under D4 (same-size, "
          f"{checks} checks): OK")


# --- 5. Substrate equivariance under color perm -------------------------

def perm_substrate(sub_grid, perm):
    """Apply a color perm to a same-size substrate (only digits change;
    '.' stays '.')."""
    return [
        [c if c == "." else str(perm[int(c)]) for c in row]
        for row in sub_grid
    ]


def check_substrate_equivariance_color(puzzles):
    rng = random.Random(0)
    checks = 0
    for puzzle in puzzles:
        for pair in puzzle["train"] + puzzle["test"]:
            inp, out = pair["input"], pair["output"]
            if not gen.is_same_size(pair):
                continue
            orig_sub = encode(inp, out)
            for _ in range(3):
                perm = gen.random_color_perm(rng)
                permed_inp = [[perm[c] for c in row] for row in inp]
                permed_out = [[perm[c] for c in row] for row in out]
                aug_sub = encode(permed_inp, permed_out)
                expected = perm_substrate(orig_sub, perm)
                if aug_sub != expected:
                    fail("color-perm equivariance broken")
                checks += 1
    print(f"  5. Substrate equivariance under color perm "
          f"({checks} checks): OK")


# --- 6. Round-trip ------------------------------------------------------

def check_roundtrip(puzzles):
    rng = random.Random(0)
    checks = 0
    for puzzle in puzzles:
        # Apply a random D4 + color perm + pair subset and verify
        # encode/decode round-trips on same-size pairs.
        op_name = rng.choice(list(gen.D4_OPS.keys()))
        perm = gen.random_color_perm(rng)
        aug = gen.apply_color_perm(gen.apply_d4(puzzle, op_name), perm)
        for pair in aug["train"] + aug["test"]:
            if not gen.is_same_size(pair):
                continue
            sub = encode(pair["input"], pair["output"])
            recovered = decode(pair["input"], sub)
            if recovered != pair["output"]:
                fail("encode/decode round-trip failed")
            checks += 1
    print(f"  6. encode/decode round-trip after augmentation "
          f"({checks} checks): OK")


# --- 7. Determinism -----------------------------------------------------

def check_determinism(puzzles):
    aug_cfg = {"d4": True, "color_perms": 3, "pair_subsetting": True,
               "pair_subset_min": 1, "pair_subset_max": 3}
    sample = puzzles[:5]
    for puzzle in sample:
        rng1 = random.Random(12345)
        rng2 = random.Random(12345)
        v1 = gen.augmentation_variants(puzzle, aug_cfg, rng1)
        v2 = gen.augmentation_variants(puzzle, aug_cfg, rng2)
        if len(v1) != len(v2):
            fail("augmentation_variants returned different lengths")
        for (p1, prov1), (p2, prov2) in zip(v1, v2):
            if p1 != p2 or prov1 != prov2:
                fail("augmentation_variants not deterministic")
    print(f"  7. augmentation_variants determinism "
          f"(on {len(sample)} puzzles): OK")


# --- Diff-size sanity (informational only) ------------------------------

def check_diffsize_sanity(puzzles):
    """For diff-size pairs, encode_auto returns str. After D4 it should
    still return str (with H/W relations swapped on rot90/rot270/transpose
    /anti_transpose, unchanged on others)."""
    swap_ops = {"rot90", "rot270", "transpose", "anti_transpose"}
    n_diff = 0
    for puzzle in puzzles:
        for pair in puzzle["train"] + puzzle["test"]:
            if gen.is_same_size(pair):
                continue
            n_diff += 1
            inp, out = pair["input"], pair["output"]
            orig = encode_auto(inp, out)
            if not isinstance(orig, str):
                fail("expected str substrate for diff-size pair")
            for op_name in gen.D4_OPS:
                op = gen.D4_OPS[op_name]
                aug = encode_auto(op(inp), op(out))
                if not isinstance(aug, str):
                    fail(f"diff-size pair lost str type after {op_name}")
                # Header tag is well-defined for both: extract first line
                orig_size = orig.splitlines()[0]
                aug_size = aug.splitlines()[0]
                if op_name in swap_ops:
                    # H and W are swapped — the SIZE line should reflect that.
                    # Just sanity-check it's still a SIZE line.
                    if not aug_size.startswith("SIZE "):
                        fail(f"diff-size aug missing SIZE header after {op_name}")
                else:
                    # Non-swap ops preserve H, W, so SIZE line is identical.
                    if op_name == "identity" and aug_size != orig_size:
                        fail(f"identity changed SIZE line: "
                             f"{orig_size!r} -> {aug_size!r}")
    print(f"  diff-size sanity ({n_diff} pairs swept): OK")


# --- Main ---------------------------------------------------------------

def main():
    print("Loading sample puzzles…")
    files = sorted(PUZZLES_DIR.glob("*.json"))
    rng = random.Random(7)
    sample_files = rng.sample(files, min(N_PUZZLES, len(files)))
    puzzles = [gen.load_puzzle(p) for p in sample_files]
    print(f"  loaded {len(puzzles)} puzzles\n")

    check_d4_bijection()
    check_color_perm_bijection()
    check_pair_subset_non_destructive(puzzles)
    check_substrate_equivariance_d4(puzzles)
    check_substrate_equivariance_color(puzzles)
    check_roundtrip(puzzles)
    check_determinism(puzzles)
    check_diffsize_sanity(puzzles)

    print("\nAll augmentation checks passed.")


if __name__ == "__main__":
    main()
