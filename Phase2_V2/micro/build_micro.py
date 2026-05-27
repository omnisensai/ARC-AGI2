"""Materialize + validate a micro-primitive family.

  python Phase2_V2/micro/build_micro.py ray_to_edge --n 60

For a family module in generators/<family>.py:
  1. write its single canonical solver to solvers/<family>.py
  2. generate N tasks across difficulty tiers (round-robin)
  3. GATE each task: run the solver vs every train+test pair (fresh subprocess)
     + AST hardcoding audit  -- the SAME gate the real corpus uses
  4. only validated tasks are written to tasks/<family>/
  5. write _validation.json + MANIFEST.txt

Validate-before-emit is the authority boundary: no pass, no task on disk.
"""
import argparse, importlib.util, json, sys
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent      # Phase2_V2/
sys.path.insert(0, str(P2 / "scripts"))
from canonical_gate import accept                 # single source of the gate

TIERS = [0, 1, 2]  # reference families use tiers 0-2 (no distractors)


def load_family(gen_dir, name):
    spec = importlib.util.spec_from_file_location(name, gen_dir / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family")
    ap.add_argument("--n", type=int, default=60, help="tasks to generate")
    ap.add_argument("--dir", default="micro", help="corpus dir under Phase2_V2/ (micro | micro_diff)")
    ap.add_argument("--big-literal-max", type=int, default=12,
                    help="AST audit literal cap; tighten (e.g. 8) for diff-size small outputs")
    a = ap.parse_args()

    ROOT = P2 / a.dir
    GEN = ROOT / "generators"; TASKS = ROOT / "tasks"; SOLV = ROOT / "solvers"
    REPORT = ROOT / "_validation.json"; MANIFEST = ROOT / "MANIFEST.txt"

    fam = load_family(GEN, a.family)
    SOLV.mkdir(parents=True, exist_ok=True)
    solver_path = SOLV / f"{a.family}.py"
    solver_path.write_text(fam.canonical_solver())

    out_dir = TASKS / a.family
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()

    kept, failed, by_tier = 0, [], {t: 0 for t in TIERS}
    for i in range(a.n):
        tier = TIERS[i % len(TIERS)]
        task = fam.generate(seed=i, difficulty=tier)
        pairs = task["train"] + task["test"]
        ok, passs, flags = accept(solver_path, pairs, big_literal_max=a.big_literal_max)
        if not ok:
            failed.append({"seed": i, "tier": tier, "pass": passs, "flags": flags})
            continue
        (out_dir / f"{a.family}_{i:05d}.json").write_text(json.dumps(task))
        kept += 1
        by_tier[tier] += 1

    rep = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    rep[a.family] = {"generated": a.n, "kept": kept, "failed": len(failed),
                     "by_tier": by_tier, "failures": failed[:10]}
    REPORT.write_text(json.dumps(rep, indent=2))

    lines = ["MICRO CORPUS — validated synthetic primitive families.",
             "Tasks here passed the SAME gate as the real corpus (solver run vs",
             "ground truth on every pair + AST audit). One solver per family.", ""]
    for f, v in sorted(rep.items()):
        lines.append(f"  {f:22s} kept {v['kept']}/{v['generated']}  by_tier {v['by_tier']}"
                     + (f"  FAILED {v['failed']}" if v['failed'] else ""))
    MANIFEST.write_text("\n".join(lines) + "\n")

    print(f"{a.family}: kept {kept}/{a.n}  failed {len(failed)}  by_tier {by_tier}")
    if failed:
        print("  FAILURES (generator/solver disagreement — investigate):")
        for fr in failed[:5]:
            print("   ", fr)


if __name__ == "__main__":
    main()
