"""Phase-2 failure funnel — turns a run's saved generations into GPT's
stage-by-stage funnel so we diagnose WHERE generation fails, not just the
final pass rate. Re-executes each emitted solve() per-pair against ground truth.

Usage:
  python "Fine Tune Run 2/phase2_funnel.py" <run_dir>
  # default: newest eval_runs/* dir

Reports counts for: has def solve, extractable, syntax-valid, ran w/o exception,
returned a grid, correct shape on >=1 pair, passed >=1 pair, passed ALL visible,
passed test; plus truncation, markdown fences, empty returns, top exception types.
Saves sample raw generations + extracted code + failure diffs for inspection.
"""
import sys, json, glob, ast, os, subprocess
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
from validate_solver import load_puzzle  # noqa

def resolve(pid, pdir):
    for suf in ("_A2E","_A2T","_A1E","_A1T",""):
        c = os.path.join(pdir, f"{pid}{suf}.json")
        if os.path.exists(c): return c
    g = glob.glob(os.path.join(pdir, f"{pid}*.json"))
    return g[0] if g else None

VRUN = r'''
import json,sys
code=sys.stdin.read(); inputs=json.loads(sys.argv[1]); ns={}
try: exec(code, ns)
except Exception as e:
    print(json.dumps({"err":f"{type(e).__name__}: {e}"})); sys.exit(0)
fn=ns.get("solve")
if fn is None: print(json.dumps({"err":"no solve()"})); sys.exit(0)
res=[]
for inp in inputs:
    try:
        o=fn(inp)
        if hasattr(o,"tolist"): o=o.tolist()
        res.append({"out":o,"err":None})
    except Exception as e: res.append({"out":None,"err":f"{type(e).__name__}: {e}"})
print(json.dumps({"res":res,"err":None}))
'''

def is_grid(g):
    return isinstance(g, list) and g and all(isinstance(r, list) for r in g) and all(g)

def main():
    run = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(ROOT,"eval_runs/*")), key=os.path.getmtime)[-1]
    pdir = sys.argv[2] if len(sys.argv) > 2 else "Fine Tune Run 2/puzzles_heldout"
    files = [f for f in sorted(glob.glob(os.path.join(run,"*.json"))) if not f.endswith("summary.json")]
    print(f"run: {run}\ngenerations: {len(files)}  puzzle-dir: {pdir}\n")

    F = Counter()
    exc = Counter()
    samples_raw, samples_code, samples_diff = [], [], []
    for f in files:
        r = json.load(open(f)); resp = r.get("response") or ""; code = r.get("code")
        F["total"] += 1
        if "def solve" in resp: F["1_has_def_solve"] += 1
        if code: F["2_extractable"] += 1
        else:
            if len(samples_raw) < 20: samples_raw.append((os.path.basename(f), resp[:800]))
            continue
        if "```" in resp: F["md_fence"] += 1
        # truncation heuristic: ends without a return / unbalanced
        if not resp.rstrip().endswith(("`", ")", "]", "return out", "out", ":")) and "return" not in code.splitlines()[-1]:
            pass
        try:
            ast.parse(code); F["3_syntax_valid"] += 1
        except Exception as e:
            exc[f"SyntaxError"] += 1
            if len(samples_code) < 20: samples_code.append((os.path.basename(f), "SYNTAX FAIL\n"+code[:800]))
            continue
        if len(samples_code) < 20: samples_code.append((os.path.basename(f), code[:800]))
        pz = load_puzzle(resolve(r["pid"], pdir))
        inputs = [p["input"] for p in pz["train"]] + [p["input"] for p in pz["test"]]
        exps   = [p["output"] for p in pz["train"]] + [p["output"] for p in pz["test"]]
        ntr = len(pz["train"])
        try:
            pr = subprocess.run([sys.executable,"-c",VRUN,json.dumps(inputs)], input=code,
                                capture_output=True, text=True, timeout=20)
            out = json.loads(pr.stdout.splitlines()[-1]) if pr.stdout.strip() else {"err":"no stdout"}
        except subprocess.TimeoutExpired:
            F["timeout"] += 1; exc["Timeout"] += 1; continue
        if out.get("err"):
            exc[out["err"].split(":")[0]] += 1; continue
        F["4_ran_no_exception"] += 1
        res = out["res"]
        if any(g["err"] for g in res): exc["per_pair_exception"] += 1
        grids = [g["out"] for g in res]
        if any(is_grid(g) for g in grids): F["5_returned_grid"] += 1
        oks = [is_grid(g) and is_grid(e) and len(g)==len(e) and all(len(gr)==len(er) for gr,er in zip(g,e)) and
               all(g[i][j]==e[i][j] for i in range(len(g)) for j in range(len(g[i]))) for g,e in zip(grids,exps)]
        shape_ok = [is_grid(g) and is_grid(e) and len(g)==len(e) and all(len(gr)==len(er) for gr,er in zip(g,e)) for g,e in zip(grids,exps)]
        if any(shape_ok): F["6_correct_shape_some"] += 1
        if any(oks): F["7_passed_ge1_pair"] += 1
        if all(oks[:ntr]): F["8_passed_all_visible"] += 1
        if all(oks[ntr:]) and all(oks[:ntr]): F["9_passed_test_too"] += 1
        if not all(oks[:ntr]) and any(shape_ok) and len(samples_diff) < 20:
            samples_diff.append((r["pid"], f"visible pass: {oks[:ntr]} | shapes: {shape_ok}"))

    print("=== FUNNEL ===")
    for k in ["total","1_has_def_solve","2_extractable","3_syntax_valid","4_ran_no_exception",
              "5_returned_grid","6_correct_shape_some","7_passed_ge1_pair","8_passed_all_visible","9_passed_test_too"]:
        print(f"  {k:24s}: {F[k]}")
    print(f"\n  markdown_fence: {F['md_fence']}  timeout: {F['timeout']}")
    print("  top exception types:", exc.most_common(10))
    out_dir = os.path.join(run, "funnel")
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"funnel":dict(F),"exceptions":dict(exc)}, open(os.path.join(out_dir,"funnel.json"),"w"), indent=2)
    json.dump(samples_raw, open(os.path.join(out_dir,"samples_no_code.json"),"w"), indent=2)
    json.dump(samples_code, open(os.path.join(out_dir,"samples_code.json"),"w"), indent=2)
    json.dump(samples_diff, open(os.path.join(out_dir,"samples_visible_fail.json"),"w"), indent=2)
    print(f"\nsaved -> {out_dir}/")

if __name__ == "__main__":
    main()
