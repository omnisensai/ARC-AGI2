"""Ceiling measurement — how often can a frontier model write ONE solver from
the train pairs that generalizes to the HELD-OUT test pair?

The model sees ONLY the training pairs (input->output). It writes solve().
Python then runs solve() on the held-out test input(s) and compares to ground
truth. The model never sees the test input or output — apply+score is mechanical.

This measures the *ceiling* of the whole approach: if a frontier model hits
N%, that's the target a distilled/fine-tuned model could aspire to, and it tells
us whether the bet (one solver from pairs generalizes) is worth investing in.

Usage:
  OPENAI_API_KEY=... python "Fine Tune Run 2/ceiling_measure.py" \
      --ids "Fine Tune Run 2/splits/phase2_dev_eval_ids.txt" \
      --puzzle-dir "Fine Tune Run 2/puzzles_heldout" \
      --model gpt-5 --attempts 2 --limit 15

Output: per-puzzle pass/fail + pass@1 / pass@k hit rate + bucket histogram.
"""
import argparse, glob, json, os, re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from validate_solver import load_puzzle  # noqa

SYSTEM = (
    "You are an expert ARC puzzle solver. You are given the training input/output "
    "pairs of one puzzle. Infer the SINGLE transformation rule that maps input to "
    "output across ALL pairs, then write one Python function `def solve(input_grid):` "
    "that implements it and generalizes to any input of this puzzle.\n"
    "Prefer this shape: read structure from the input (objects, regions, symmetry, "
    "repetition, markers), infer the transformation it implies, build the output. "
    "Do NOT hardcode outputs or special-case specific grids. input_grid is a "
    "list[list[int]] (0-9). Return ONLY one ```python code block, nothing else."
)

def grid_str(g): return "\n".join(" ".join(str(c) for c in row) for row in g)

def build_prompt(pz):
    parts = []
    for i, p in enumerate(pz["train"]):
        parts.append(f"Training pair {i+1}:\nInput:\n{grid_str(p['input'])}\n\nOutput:\n{grid_str(p['output'])}")
    return "\n\n".join(parts) + "\n\nWrite def solve(input_grid):"

CODE = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.DOTALL)
def extract(text):
    m = CODE.findall(text)
    if m: return m[-1]
    return text[text.index("def solve"):] if "def solve" in text else None

VRUN = r'''
import json,sys
code=sys.stdin.read(); inputs=json.loads(sys.argv[1]); ns={}
try: exec(code, ns)
except Exception as e: print(json.dumps({"err":f"{type(e).__name__}: {e}"})); sys.exit(0)
fn=ns.get("solve")
if fn is None: print(json.dumps({"err":"no solve()"})); sys.exit(0)
res=[]
for inp in inputs:
    try:
        o=fn(inp)
        if hasattr(o,"tolist"): o=o.tolist()
        res.append(o)
    except Exception as e: res.append({"__err__":f"{type(e).__name__}: {e}"})
print(json.dumps({"res":res}))
'''

def eq(a, b):
    return (isinstance(a, list) and a and isinstance(a[0], list)
            and len(a) == len(b) and all(len(x)==len(y) for x,y in zip(a,b))
            and all(a[r][c]==b[r][c] for r in range(len(a)) for c in range(len(a[r]))))

def run_solver(code, pz):
    ins = [p["input"] for p in pz["train"]] + [p["input"] for p in pz["test"]]
    exps = [p["output"] for p in pz["train"]] + [p["output"] for p in pz["test"]]
    ntr = len(pz["train"])
    try:
        r = subprocess.run([sys.executable,"-c",VRUN,json.dumps(ins)], input=code,
                           capture_output=True, text=True, timeout=25)
        out = json.loads(r.stdout.splitlines()[-1]) if r.stdout.strip() else {"err":"no stdout"}
    except subprocess.TimeoutExpired:
        return {"bucket":"exec_error","train_pass":False,"test_pass":False,"err":"timeout"}
    if out.get("err"): return {"bucket":"exec_error","train_pass":False,"test_pass":False,"err":out["err"]}
    res = out["res"]
    ok = [eq(g, e) for g, e in zip(res, exps)]
    tr, te = all(ok[:ntr]), all(ok[ntr:])
    return {"bucket": "correct" if (tr and te) else "wrong_test" if tr else "wrong_training",
            "train_pass": tr, "test_pass": te, "err": None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True)
    ap.add_argument("--puzzle-dir", default="Fine Tune Run 2/puzzles_heldout")
    ap.add_argument("--model", default="gpt-5")
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--same-only", action="store_true", default=True)
    args = ap.parse_args()

    from openai import OpenAI
    client = OpenAI()

    def resolve(pid):
        for suf in ("_A2E","_A2T","_A1E","_A1T",""):
            c = Path(args.puzzle_dir)/f"{pid}{suf}.json"
            if c.exists(): return str(c)
        g = glob.glob(f"{args.puzzle_dir}/{pid}*.json"); return g[0] if g else None

    ids = [x.strip() for x in Path(args.ids).read_text().split() if x.strip()][:args.limit*3]
    puzzles = {}
    for pid in ids:
        f = resolve(pid)
        if not f: continue
        pz = load_puzzle(f)
        same = all(len(p["input"])==len(p["output"]) and len(p["input"][0])==len(p["output"][0]) for p in pz["train"])
        if args.same_only and not same: continue
        puzzles[pid] = pz
        if len(puzzles) >= args.limit: break
    print(f"measuring ceiling on {len(puzzles)} puzzles x {args.attempts} attempts, model={args.model}\n")

    rows = []
    for pid, pz in puzzles.items():
        prompt = build_prompt(pz)
        best = None
        for a in range(args.attempts):
            try:
                resp = client.chat.completions.create(
                    model=args.model, temperature=args.temperature,
                    messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
                ).choices[0].message.content
            except Exception as e:
                print(f"  {pid} a{a}: API error {e}"); continue
            code = extract(resp)
            r = {"bucket":"no_code"} if not code else run_solver(code, pz)
            r["code"] = code
            print(f"  {pid} a{a} -> {r['bucket']}" + (f" ({r.get('err')})" if r.get('err') else ""))
            if best is None or (r["bucket"]=="correct"): best = r
        rows.append((pid, best or {"bucket":"no_code"}))

    n = len(rows)
    solved = [pid for pid,r in rows if r["bucket"]=="correct"]
    from collections import Counter
    hist = Counter(r["bucket"] for _,r in rows)
    print("\n=== CEILING ===")
    print(f"  puzzles: {n}")
    print(f"  pass@{args.attempts} (CORRECT, generalized to held-out test): {len(solved)}/{n} = {round(100*len(solved)/max(n,1),1)}%")
    print(f"  buckets: {dict(hist)}")
    print(f"  solved: {solved}")
    Path("ceiling_results.json").write_text(json.dumps(
        {"model":args.model,"n":n,"pass":len(solved),"pct":round(100*len(solved)/max(n,1),1),
         "buckets":dict(hist),"solved":solved,
         "rows":[{"pid":p,"bucket":r["bucket"],"code":r.get("code")} for p,r in rows]}, indent=2))
    print("  -> ceiling_results.json")

if __name__ == "__main__":
    main()
