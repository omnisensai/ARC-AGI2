"""Incremental verifier for the canonical latent-T corpus (Phase2_V2).

Re-runs each NEW solver in canonical/solvers/ against ALL its puzzle pairs
(independent of the agent's claim) + AST-audits it, recording the verdict in
canonical/_validation.json (only checks solvers not already recorded, so it's
cheap to run every refill). Prints a corpus summary + the next TODO ids to launch.

  python Phase2_V2/scripts/validate_canonical.py [--next N]
"""
import argparse, ast, glob, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent  # = Phase2_V2/
SOLV = ROOT / "canonical/solvers"
TASKS = ROOT / "canonical/_tasks"
REPORT = ROOT / "canonical/_validation.json"
IDS = ROOT / "splits/golden_train_ids.txt"

VRUN = r'''
import json,sys
exec(open(sys.argv[1]).read(), (ns:={}))
pairs=json.load(open(sys.argv[2])); fn=ns.get("solve")
oks=[]
for p in pairs:
    try:
        o=fn(p["input"]); o=o.tolist() if hasattr(o,"tolist") else o
        oks.append(o==p["output"])
    except Exception: oks.append(False)
print(json.dumps(oks))
'''
open("/tmp/_vc.py","w").write(VRUN)

def audit(code):
    flags=[]
    try: t=ast.parse(code)
    except: return ["unparseable"]
    def gl(n):
        if not isinstance(n,ast.List): return 0
        s=0
        for e in n.elts:
            if isinstance(e,ast.List): s+=len(e.elts)
            else: return 0
        return s
    big=0; eq=False
    for n in ast.walk(t):
        big=max(big,gl(n))
        if isinstance(n,ast.Compare):
            for op,c in zip(n.ops,n.comparators):
                if isinstance(op,(ast.Eq,ast.NotEq)) and gl(c)>=9: eq=True
    if big>=12: flags.append(f"BIG_LITERAL({big})")
    if eq: flags.append("EQ_GRID")
    if "frozenset(" in code and ("known" in code.lower() or "case" in code.lower()): flags.append("FINGERPRINT")
    import re
    if not re.search(r"\b(infer_T|apply_T|mask|changes|delta|T\s*=|Tcells)\b", code): flags.append("NO_MASK")
    return flags

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--next", type=int, default=0); a=ap.parse_args()
    rep=json.loads(REPORT.read_text()) if REPORT.exists() else {}
    for f in sorted(SOLV.glob("*.py")):
        pid=f.stem
        if pid.startswith("_") or pid in rep: continue
        task=TASKS/f"{pid}.json"
        if not task.exists(): rep[pid]={"status":"no_task"}; continue
        npairs=len(json.load(open(task))["train"])+len(json.load(open(task))["test"])
        json.dump(json.load(open(task))["train"]+json.load(open(task))["test"], open("/tmp/_pairs.json","w"))
        try:
            r=subprocess.run([sys.executable,"/tmp/_vc.py",str(f),"/tmp/_pairs.json"],capture_output=True,text=True,timeout=60)
            oks=json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else [False]*npairs
        except subprocess.TimeoutExpired: oks=[False]*npairs
        flags=audit(f.read_text())
        hardbad=any(x.startswith(("BIG_LITERAL","EQ_GRID","FINGERPRINT","NO_MASK","unparseable")) for x in flags)
        rep[pid]={"status":"accepted" if (all(oks) and not hardbad) else "rejected",
                  "pass":f"{sum(oks)}/{len(oks)}","flags":flags}
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
