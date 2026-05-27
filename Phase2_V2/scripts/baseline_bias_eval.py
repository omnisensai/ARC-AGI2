"""Baseline bias eval — score model-generated solvers for CORRECTNESS *and* CODE BIAS.

The existing runner buckets generations correct/wrong; it does NOT tell you whether
a "correct" solver actually inferred a rule or just hardcoded the grid. For choosing
a base model (e.g. Qwen-Instruct vs Qwen-Coder) the second question is the point:
a code-biased model can score by memorising/pattern-matching, which is worthless
for generalisation.

This reads a bulk_collect-style directory of per-generation JSON ({puzzle_id, code,
bucket}) and reports, over all generations and per puzzle:
  - solve rate (test_pass via the recorded bucket)
  - HARDCODE rate (AST audit: BIG_LITERAL / EQ_GRID / FINGERPRINT — a literal output
    grid, an `input == [...]` memorised branch, or a fingerprint/lookup)
  - the cross-tab that matters: of the CORRECT solvers, how many are honest vs cheats

NO_MASK/unparseable from the canonical gate are ignored here — they are about *our*
canonical style, not about a raw model cheating.

Usage:
    python Phase2_V2/scripts/baseline_bias_eval.py <generations_dir> [--big-literal-max 12]
"""
import argparse, glob, json, os, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canonical_gate import audit                     # reuse the same AST audit

HARDCODE = ("BIG_LITERAL", "EQ_GRID", "FINGERPRINT")  # the code-bias signals


def load_generations(d):
    gens = []
    for f in glob.glob(os.path.join(d, "**", "*.json"), recursive=True):
        if os.path.basename(f) in ("summary.json", "run_meta.json"):
            continue
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if "code" not in r or "puzzle_id" not in r:
            continue
        gens.append(r)
    return gens


def is_correct(r):
    b = r.get("bucket", "")
    return b == "correct"                              # test_pass AND train_pass


def hardcode_flags(code, big_literal_max):
    if not code or not isinstance(code, str):
        return []
    return [f for f in audit(code, big_literal_max) if f.startswith(HARDCODE)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gens_dir")
    ap.add_argument("--big-literal-max", type=int, default=12)
    a = ap.parse_args()

    gens = load_generations(a.gens_dir)
    if not gens:
        print(f"no generations found under {a.gens_dir}"); return

    n = len(gens)
    model = Counter(r.get("model", "?") for r in gens).most_common(1)[0][0]
    correct = [r for r in gens if is_correct(r)]
    hardcoded = [r for r in gens if hardcode_flags(r.get("code"), a.big_literal_max)]
    correct_ids = set(r["puzzle_id"] for r in correct)
    all_ids = set(r["puzzle_id"] for r in gens)

    cheat_solves = [r for r in correct if hardcode_flags(r.get("code"), a.big_literal_max)]
    honest_solves = [r for r in correct if not hardcode_flags(r.get("code"), a.big_literal_max)]

    print(f"model: {model}")
    print(f"generations: {n}   puzzles: {len(all_ids)}\n")
    print(f"  correct (solve@gen):     {len(correct):5d} / {n}  ({100*len(correct)/n:.1f}%)")
    print(f"  puzzles solved (solve@k):{len(correct_ids):5d} / {len(all_ids)}  ({100*len(correct_ids)/len(all_ids):.1f}%)")
    print(f"  HARDCODE rate (all gens):{len(hardcoded):5d} / {n}  ({100*len(hardcoded)/n:.1f}%)   <- code bias")
    print()
    print("  --- of the CORRECT solvers ---")
    if correct:
        print(f"     honest (rule-based):  {len(honest_solves):4d}  ({100*len(honest_solves)/len(correct):.1f}%)")
        print(f"     CHEAT (hardcoded):    {len(cheat_solves):4d}  ({100*len(cheat_solves)/len(correct):.1f}%)   <- inflated/worthless")
    else:
        print("     (no correct solvers in this run)")
    flagcount = Counter(f.split("(")[0] for r in gens for f in hardcode_flags(r.get("code"), a.big_literal_max))
    if flagcount:
        print("\n  hardcode flag breakdown:", dict(flagcount))


if __name__ == "__main__":
    main()
