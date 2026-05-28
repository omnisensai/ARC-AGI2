"""Augment ONE canonical solver's puzzle pairs via D4 + color permutation.

Pilot script: validates the augmentation pipeline end-to-end on a single
puzzle before running the full corpus.

  python Phase2_V2/canonical/augment_one.py 00d62c1b

For each (D4 transform, color permutation) combination:
  1. apply the transform to every train+test pair
  2. run the canonical solver on the augmented pairs (same gate as build_micro)
  3. keep augmentations where the solver still passes ALL pairs

This is how we tell a canonical solver from a fingerprint: a real canonical
solver survives the symmetries its rule respects; a fingerprint dies.
"""
import argparse, json, random, sys
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent  # Phase2_V2/
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import accept
sys.path.insert(0, str(P2 / "micro"))
from build_micro_sft import SYSTEM, render_pairs, variants  # reuse renderer

# ---- D4 ----------------------------------------------------------------
def _id(g):      return [row[:] for row in g]
def _rot90(g):   return [list(r) for r in zip(*g[::-1])]
def _rot180(g):  return [row[::-1] for row in g[::-1]]
def _rot270(g):  return [list(r) for r in zip(*g)][::-1]
def _flip_h(g):  return [row[::-1] for row in g]
def _flip_v(g):  return g[::-1]
def _trans(g):   return [list(r) for r in zip(*g)]
def _antitr(g):  return [list(r) for r in zip(*[row[::-1] for row in g[::-1]])]

D4 = [("id", _id), ("rot90", _rot90), ("rot180", _rot180), ("rot270", _rot270),
      ("fliph", _flip_h), ("flipv", _flip_v), ("trans", _trans), ("antitr", _antitr)]


# ---- color permutation -------------------------------------------------
def color_perm(g, perm):
    return [[perm.get(v, v) for v in row] for row in g]

def random_perm(rng):
    """Shuffle 1..9; keep 0 (background convention) fixed."""
    cs = list(range(1, 10)); rng.shuffle(cs)
    return {0: 0, **{i + 1: cs[i] for i in range(9)}}


# ---- main --------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("puzzle_id")
    ap.add_argument("--color-perms", type=int, default=4,
                    help="random color permutations to try (plus identity)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--emit-sft", type=str, default=None,
                    help="if set, also write SFT records to this path")
    a = ap.parse_args()

    solver_path = P2 / "canonical" / "solvers" / f"{a.puzzle_id}.py"
    puzzle_path = P2 / "canonical" / "ground_truth_puzzles" / f"{a.puzzle_id}.json"
    if not solver_path.exists() or not puzzle_path.exists():
        print(f"ERROR: missing solver or puzzle for {a.puzzle_id}", file=sys.stderr)
        sys.exit(1)

    puzzle = json.loads(puzzle_path.read_text())
    all_pairs = puzzle["train"] + puzzle["test"]
    rng = random.Random(a.seed)

    perms = [("c_id", {i: i for i in range(10)})]
    for k in range(a.color_perms):
        perms.append((f"c_p{k}", random_perm(rng)))

    accepted, rejected = [], []
    for d4_name, d4_fn in D4:
        for c_name, c_perm in perms:
            aug = [{"input":  color_perm(d4_fn(p["input"]),  c_perm),
                    "output": color_perm(d4_fn(p["output"]), c_perm)}
                   for p in all_pairs]
            ok, passes, flags = accept(solver_path, aug)
            tag = f"{d4_name}+{c_name}"
            if ok:
                accepted.append((tag, aug))
            else:
                rejected.append((tag, passes, flags))

    total = len(D4) * len(perms)
    print(f"\n=== {a.puzzle_id} ===")
    print(f"attempted: {total}    accepted: {len(accepted)}    rejected: {len(rejected)}")
    print(f"\nACCEPTED ({len(accepted)}):")
    for tag, _ in accepted:
        print(f"  {tag}")
    print(f"\nREJECTED (showing up to 10):")
    for tag, passes, flags in rejected[:10]:
        print(f"  {tag}  pairs {passes}  flags {flags}")
    print(f"\n[ {len(accepted)}/{total} augmentations survived the gate ]")

    if a.emit_sft:
        solver_src = solver_path.read_text()
        n_train_orig = len(puzzle["train"])
        out_path = Path(a.emit_sft)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        n_rec, by_variant = 0, {}
        with out_path.open("w") as fh:
            for tag, aug in accepted:
                # split augmented pairs back into train/test by original sizes
                aug_train = aug[:n_train_orig]
                aug_test  = aug[n_train_orig:]
                for label, shown, _ in variants(aug_train, aug_test, rng):
                    user = render_pairs(shown) + "\n\nWrite def solve(input_grid)."
                    rec = {"system": SYSTEM, "user": user, "assistant": solver_src,
                           "meta": {"puzzle": a.puzzle_id, "augment": tag, "variant": label}}
                    fh.write(json.dumps(rec) + "\n")
                    n_rec += 1
                    by_variant[label] = by_variant.get(label, 0) + 1
        print(f"\nSFT: {n_rec} records ({len(accepted)} aug x variants) -> {out_path}")
        print(f"  by variant: {by_variant}")


if __name__ == "__main__":
    main()
