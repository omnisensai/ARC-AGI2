"""Robust proximity analyzer for run_eval_lora outputs.

Reads all per-attempt JSONs in a run directory, re-executes the model's code,
and reports cell-level accuracy distribution. Skips partial/corrupt files.

Usage:
    python scripts/analyze_proximity.py                          # latest run
    python scripts/analyze_proximity.py --run eval_runs/<dir>    # specific run

Companion to research/case_studies/arc_lora_run1_locked_eval.md
"""
import argparse, json, subprocess, sys
from pathlib import Path
from collections import Counter

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

def run_code(code, inputs, timeout=20):
    try:
        r = subprocess.run([sys.executable, "-c", VRUN, json.dumps(inputs)],
                           input=code, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if not r.stdout.strip():
        return None, "no_stdout"
    try:
        out = json.loads(r.stdout.splitlines()[-1])
    except Exception:
        return None, "bad_runner_json"
    if out.get("error"):
        return None, out["error"][:40]
    return out["results"], None

def cell_pct(got, exp):
    if not isinstance(got, list) or not got or not isinstance(got[0], list):
        return None
    if len(got) != len(exp) or any(len(g)!=len(e) for g,e in zip(got, exp)):
        return -1.0
    diffs = sum(1 for r in range(len(exp)) for c in range(len(exp[0])) if got[r][c]!=exp[r][c])
    total = sum(len(row) for row in exp)
    return 100*(total-diffs)/total

def analyze(run_dir, puzzle_dir):
    files = sorted(Path(run_dir).glob("*__a*.json"))
    bucket = Counter()
    pct_list = []
    near_miss = []
    skipped = 0
    for f in files:
        if f.stat().st_size == 0:
            skipped += 1; continue
        try:
            rec = json.load(open(f))
        except Exception:
            skipped += 1; continue
        code = rec.get("code")
        pid = rec.get("pid","?"); att = rec.get("attempt","?")
        if not code:
            bucket["no_code"] += 1; continue
        pf = Path(puzzle_dir) / f"{pid}.json"
        if not pf.exists():
            bucket["puzzle_missing"] += 1; continue
        puz = json.load(open(pf))
        inputs = [p["input"] for p in puz["train"]] + [p["input"] for p in puz["test"]]
        expecteds = [p["output"] for p in puz["train"]] + [p["output"] for p in puz["test"]]
        n_train = len(puz["train"])
        results, err = run_code(code, inputs)
        if err:
            bucket["exec_error"] += 1; continue
        train_pcts = []
        test_pcts  = []
        for i,(g,e) in enumerate(zip(results, expecteds)):
            kind = "train" if i<n_train else "test"
            if g["error"]:
                p = -1.0
            else:
                a = cell_pct(g["output"], e)
                p = a if a is not None else -1.0
            (train_pcts if kind=="train" else test_pcts).append(p)
        good_train = [x for x in train_pcts if x>=0]
        if not good_train:
            bucket["train_no_grid"] += 1; continue
        avg = sum(good_train)/len(good_train)
        if all(x==100.0 for x in train_pcts) and test_pcts and all(x==100.0 for x in test_pcts):
            bucket["CORRECT"] += 1
        elif all(x==100.0 for x in train_pcts):
            bucket["train_pass_test_fail"] += 1
        else:
            bucket["wrong_training"] += 1
            if avg >= 95: near_miss.append((pid, att, avg))
        pct_list.append(avg)
    n = sum(bucket.values())
    print(f"Analyzed {n} attempts (skipped {skipped} partial/corrupt)\n")
    print("Bucket breakdown:")
    for k,v in bucket.most_common():
        print(f"  {k:35s} {v}")
    print(f"\nNear-miss (>= 95% avg train cell-accuracy): {len(near_miss)}")
    for pid,att,avg in sorted(near_miss, key=lambda x:-x[2])[:30]:
        print(f"  {pid} a{att}  {avg:.1f}%")
    if pct_list:
        print(f"\nAvg-train-acc histogram (n={len(pct_list)}):")
        b = [0]*11
        for p in pct_list:
            b[min(10,int(p//10))] += 1
        for i,c in enumerate(b):
            label = f"{i*10:3d}-{(i+1)*10:3d}%" if i<10 else "100%   "
            print(f"  {label}  {c:4d}  {'#'*c}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--puzzle-dir", default="data/arc2_eval")
    args = ap.parse_args()
    run = args.run or str(sorted(Path("eval_runs").iterdir(), key=lambda p: p.stat().st_mtime)[-1])
    print(f"Analyzing: {run}\n")
    analyze(run, args.puzzle_dir)
