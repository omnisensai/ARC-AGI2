"""Diff-size pilot: validate hand-written canonical solvers on REAL puzzles.

Parses the Puzzle_Database flattened format (flat list of single-char strings
with '\\n' separator tokens) into 2D int grids, then runs each solver through the
SAME canonical gate as the rest of the corpus (solver vs ground-truth output in
a fresh subprocess + AST audit), with the diff-size literal cap (8).

Each solver is tested against EVERY augmentation variant file of its puzzle id,
so we measure real algorithmic robustness, not a single-file fit.
"""
import glob, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent.parent                       # Phase2_V2/
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import accept

DB = P2 / "Puzzle_Database"
SOLV = HERE / "solvers"


def parse(flat):
    rows, cur = [], []
    for tok in flat:
        if tok == "\n":
            rows.append(cur); cur = []
        else:
            cur.append(int(tok))
    if cur:
        rows.append(cur)
    return rows


def pairs_from_file(f):
    d = json.loads(Path(f).read_text())
    out = []
    for sec in ("train", "test"):
        for p in d.get(sec, []):
            out.append({"input": parse(p["input"]), "output": parse(p["output"])})
    return out


def main():
    ids = sorted(p.stem for p in SOLV.glob("*.py"))
    print(f"diff-size pilot — {len(ids)} solvers, gate big_literal_max=8\n")
    grand_ok = 0
    grand_files = 0
    for pid in ids:
        solver = SOLV / f"{pid}.py"
        variants = sorted(glob.glob(str(DB / f"{pid}_*.json")))
        results = []
        for vf in variants:
            pairs = pairs_from_file(vf)
            ok, passs, flags = accept(solver, pairs, big_literal_max=8)
            results.append((Path(vf).name, ok, passs, flags))
            grand_files += 1
            grand_ok += ok
        passed = sum(1 for _, ok, _, _ in results if ok)
        print(f"  {pid}: {passed}/{len(results)} variant files PASS")
        for name, ok, passs, flags in results:
            mark = "OK " if ok else "XX "
            print(f"      {mark}{name:24s} pairs {passs}  flags {flags}")
    print(f"\nTOTAL: {grand_ok}/{grand_files} variant files validated.")


if __name__ == "__main__":
    main()
