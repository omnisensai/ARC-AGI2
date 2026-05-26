"""Incremental verifier for the canonical latent-T corpus (Phase2_V2).

Re-runs each NEW solver in canonical/solvers/ against ALL its puzzle pairs
(independent of the agent's claim) + AST-audits it, recording the verdict in
canonical/_validation.json (only checks solvers not already recorded, so it's
cheap to run every refill). Prints a corpus summary + the next TODO ids to launch.

  python Phase2_V2/scripts/validate_canonical.py [--next N]
"""
import argparse, glob, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from canonical_gate import accept  # single source of the acceptance gate

ROOT = Path(__file__).resolve().parent.parent  # = Phase2_V2/
SOLV = ROOT / "canonical/solvers"
TASKS = ROOT / "canonical/ground_truth_puzzles"
REPORT = ROOT / "canonical/_validation.json"
IDS = ROOT / "splits/golden_train_ids.txt"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--next", type=int, default=0); a=ap.parse_args()
    rep=json.loads(REPORT.read_text()) if REPORT.exists() else {}
    for f in sorted(SOLV.glob("*.py")):
        pid=f.stem
        if pid.startswith("_") or pid in rep: continue
        task=TASKS/f"{pid}.json"
        if not task.exists(): rep[pid]={"status":"no_task"}; continue
        d=json.load(open(task)); pairs=d["train"]+d["test"]
        ok, passs, flags = accept(f, pairs)
        rep[pid]={"status":"accepted" if ok else "rejected","pass":passs,"flags":flags}
    REPORT.write_text(json.dumps(rep,indent=2))
    acc=[p for p,v in rep.items() if v.get("status")=="accepted"]
    rej=[p for p,v in rep.items() if v.get("status")=="rejected"]
    ids=[x.strip() for x in IDS.read_text().split() if x.strip()]
    have={f.stem for f in SOLV.glob("*.py") if not f.stem.startswith("_")}
    todo=[p for p in ids if p not in have]
    print(f"corpus: {len(ids)} target | {len(have)} solvers written | accepted {len(acc)} | rejected {len(rej)} | TODO {len(todo)}")
    if rej: print("  rejected:", rej)
    if a.next: print("NEXT:", " ".join(todo[:a.next]))

if __name__=="__main__": main()
