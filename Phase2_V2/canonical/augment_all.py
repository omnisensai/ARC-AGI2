"""Run the D4 + color augmentation pipeline across all 740 canonical solvers.

Same logic as augment_one.py, applied to every puzzle:
  - For each (D4 transform, color permutation): re-run the canonical solver
    on the augmented pairs in a fresh subprocess (canonical_gate.accept).
  - Keep augmentations where the solver still passes ALL pairs.
  - Emit one SFT record per (accepted aug, pair-subsample variant).

Output:
  Phase2_V2/canonical/sft/real_samesize.jsonl   — pooled SFT records
  Phase2_V2/canonical/augment_report.json       — per-puzzle accept counts

  python Phase2_V2/canonical/augment_all.py [--color-perms 4] [--seed 0]
"""
import argparse, json, random, sys, time
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import accept
sys.path.insert(0, str(P2 / "micro"))
from build_micro_sft import SYSTEM, render_pairs, variants

# D4
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


def color_perm(g, perm):
    return [[perm.get(v, v) for v in row] for row in g]

def random_perm(rng):
    cs = list(range(1, 10)); rng.shuffle(cs)
    return {0: 0, **{i + 1: cs[i] for i in range(9)}}


def augment_puzzle(puzzle_id, solver_path, puzzle, color_perms, rng):
    """Return list of (tag, aug_train, aug_test) that survived the gate."""
    all_pairs = puzzle["train"] + puzzle["test"]
    n_train = len(puzzle["train"])
    perms = [("c_id", {i: i for i in range(10)})]
    for k in range(color_perms):
        perms.append((f"c_p{k}", random_perm(rng)))

    accepted = []
    n_attempt = len(D4) * len(perms)
    for d4_name, d4_fn in D4:
        for c_name, c_perm in perms:
            aug = [{"input":  color_perm(d4_fn(p["input"]),  c_perm),
                    "output": color_perm(d4_fn(p["output"]), c_perm)}
                   for p in all_pairs]
            ok, _, _ = accept(solver_path, aug)
            if ok:
                accepted.append((f"{d4_name}+{c_name}", aug[:n_train], aug[n_train:]))
    return accepted, n_attempt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--color-perms", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="Phase2_V2/canonical/sft/real_samesize.jsonl")
    ap.add_argument("--report", default="Phase2_V2/canonical/augment_report.json")
    ap.add_argument("--limit", type=int, default=0, help="cap puzzles (0 = all)")
    a = ap.parse_args()

    SOLV = P2 / "canonical" / "solvers"
    PUZ  = P2 / "canonical" / "ground_truth_puzzles"
    ids = sorted(p.stem for p in SOLV.glob("*.py"))
    if a.limit:
        ids = ids[:a.limit]

    out_path = Path(a.out); out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {}
    n_total_rec, n_total_aug = 0, 0
    t0 = time.time()
    with out_path.open("w") as fh:
        for i, pid in enumerate(ids):
            solver_path = SOLV / f"{pid}.py"
            puzzle_path = PUZ / f"{pid}.json"
            if not puzzle_path.exists():
                report[pid] = {"error": "no puzzle"}; continue
            puzzle = json.loads(puzzle_path.read_text())
            rng = random.Random(a.seed + i)  # deterministic per puzzle
            accepted, n_attempt = augment_puzzle(pid, solver_path, puzzle,
                                                  a.color_perms, rng)
            solver_src = solver_path.read_text()
            n_rec = 0
            for tag, aug_train, aug_test in accepted:
                for label, shown, _ in variants(aug_train, aug_test, rng):
                    user = render_pairs(shown) + "\n\nWrite def solve(input_grid)."
                    rec = {"system": SYSTEM, "user": user, "assistant": solver_src,
                           "meta": {"puzzle": pid, "augment": tag, "variant": label}}
                    fh.write(json.dumps(rec) + "\n")
                    n_rec += 1
            report[pid] = {"accepted": len(accepted), "attempted": n_attempt,
                           "records": n_rec}
            n_total_rec += n_rec
            n_total_aug += len(accepted)
            if (i + 1) % 50 == 0:
                dt = time.time() - t0
                eta = dt / (i + 1) * (len(ids) - i - 1)
                print(f"[{i+1}/{len(ids)}] aug={n_total_aug} rec={n_total_rec} "
                      f"  {dt:.0f}s elapsed  eta {eta:.0f}s")

    Path(a.report).write_text(json.dumps(report, indent=2))
    dt = time.time() - t0
    print(f"\n=== DONE in {dt:.0f}s ===")
    print(f"puzzles: {len(ids)}")
    print(f"total augmentations accepted: {n_total_aug}")
    print(f"total SFT records: {n_total_rec}")
    print(f"avg records / puzzle: {n_total_rec / max(1, len(ids)):.1f}")
    # distribution
    buckets = {"0": 0, "1-10": 0, "11-20": 0, "21-30": 0, "31-40": 0}
    for pid, v in report.items():
        if "accepted" not in v: continue
        a_ = v["accepted"]
        b = "0" if a_ == 0 else ("1-10" if a_ <= 10 else "11-20" if a_ <= 20
                                 else "21-30" if a_ <= 30 else "31-40")
        buckets[b] += 1
    print(f"acceptance distribution (out of 40): {buckets}")


if __name__ == "__main__":
    main()
