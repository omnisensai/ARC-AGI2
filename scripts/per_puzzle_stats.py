"""Per-puzzle cell-accuracy table across saved eval attempts.

For each unique puzzle in the run dir, prints best train cell-accuracy
and per-attempt status. Sorted with CORRECT puzzles first then by best %.

Usage:
    python scripts/per_puzzle_stats.py                          # latest run
    python scripts/per_puzzle_stats.py --run eval_runs/<dir>    # specific run
"""
import argparse, json, subprocess, sys
from pathlib import Path
from collections import defaultdict

VRUN = r'''
import json,sys
code=sys.stdin.read(); inputs=json.loads(sys.argv[1]); ns={}
try: exec(code, ns)
except Exception as e:
    print(json.dumps({"error": f"exec: {type(e).__name__}: {e}"})); sys.exit(0)
fn=ns.get("solve")
if fn is None:
    print(json.dumps({"error":"no solve()"})); sys.exit(0)
out=[]
for inp in inputs:
    try:
        o=fn(inp)
        if hasattr(o,"tolist"): o=o.tolist()
        out.append({"output":o,"error":None})
    except Exception as e:
        out.append({"output":None,"error":f"{type(e).__name__}: {e}"})
print(json.dumps({"results":out,"error":None}))
'''

def run_code(code, inputs, t=20):
    try:
        r = subprocess.run([sys.executable, "-c", VRUN, json.dumps(inputs)],
                           input=code, capture_output=True, text=True, timeout=t)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if not r.stdout.strip(): return None, "no_stdout"
    try:
        out = json.loads(r.stdout.splitlines()[-1])
    except Exception:
        return None, "bad_runner_json"
    if out.get("error"): return None, out["error"][:40]
    return out["results"], None

def cell_pct(got, exp):
    if not isinstance(got, list) or not got or not isinstance(got[0], list): return None
    if len(got) != len(exp) or any(len(g)!=len(e) for g,e in zip(got, exp)): return -1.0
    diffs = sum(1 for r in range(len(exp)) for c in range(len(exp[0])) if got[r][c]!=exp[r][c])
    total = sum(len(row) for row in exp)
    return 100*(total-diffs)/total

def analyze(run_dir, puzzle_dir):
    files = sorted(Path(run_dir).glob("*__a*.json"))
    by_pid = defaultdict(list)
    for f in files:
        if f.stat().st_size == 0: continue
        try: rec = json.load(open(f))
        except Exception: continue
        by_pid[rec["pid"]].append(rec)
    print(f"{len(by_pid)} puzzles, {sum(len(v) for v in by_pid.values())} attempts\n")
    rows = []
    for pid, attempts in by_pid.items():
        pf = Path(puzzle_dir)/f"{pid}.json"
        if not pf.exists(): continue
        puz = json.load(open(pf))
        inputs = [p["input"] for p in puz["train"]] + [p["input"] for p in puz["test"]]
        expecteds = [p["output"] for p in puz["train"]] + [p["output"] for p in puz["test"]]
        n_train = len(puz["train"])
        best, atts, correct = -2.0, [], False
        for rec in sorted(attempts, key=lambda r: r["attempt"]):
            code = rec.get("code")
            if not code: atts.append((rec["attempt"], "no_code")); continue
            res, err = run_code(code, inputs)
            if err: atts.append((rec["attempt"], err)); continue
            train_pcts, test_pcts = [], []
            for i,(g,e) in enumerate(zip(res, expecteds)):
                kind = "train" if i<n_train else "test"
                p = (cell_pct(g["output"], e) if not g["error"] else -1.0) or -1.0
                (train_pcts if kind=="train" else test_pcts).append(p)
            good = [x for x in train_pcts if x>=0]
            if not good: atts.append((rec["attempt"], "no_grid")); continue
            avg = sum(good)/len(good)
            train_all = all(x==100.0 for x in train_pcts)
            test_all = test_pcts and all(x==100.0 for x in test_pcts)
            if train_all and test_all: correct = True; atts.append((rec["attempt"], "CORRECT"))
            elif train_all: atts.append((rec["attempt"], "train_pass_test_fail"))
            else: atts.append((rec["attempt"], f"{avg:.1f}%"))
            best = max(best, avg)
        rows.append((pid, best, atts, correct))
    rows.sort(key=lambda r: (-int(r[3]), -r[1]))
    print(f"{'PID':<10}  {'best%':>6}  attempts")
    print("-"*90)
    n_correct = 0
    for pid, best, atts, c in rows:
        if c: n_correct += 1
        flag = " *CORRECT" if c else ""
        att_str = "  ".join(f"a{a}={t}" for a,t in atts)
        b = f"{best:>5.1f}" if best>=0 else "  n/a"
        print(f"{pid:<10}  {b}  {att_str}{flag}")
    print(f"\npass@any = {n_correct}/{len(rows)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--puzzle-dir", default="data/arc2_eval")
    args = ap.parse_args()
    run = args.run or str(sorted(Path("eval_runs").iterdir(), key=lambda p: p.stat().st_mtime)[-1])
    print(f"Analyzing: {run}\n")
    analyze(run, args.puzzle_dir)
