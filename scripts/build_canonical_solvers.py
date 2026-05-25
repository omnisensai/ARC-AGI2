"""Build canonical latent-T solvers via an LLM, verified against all pairs.

For each same-size puzzle: prompt an LLM (input->output pairs + explicit T +
canonical exemplars) -> get a `solve()` in canonical `infer_T/apply_T` shape ->
execute against ALL pairs -> if it fails, feed the failing-pair diff back and
retry (repair loop) -> AST-audit to reject hardcoding / require a visible
transformation mask -> save accepted solvers as canonical training targets.

GPU-free; runs anywhere with an LLM API key.

  OPENAI_API_KEY=... python scripts/build_canonical_solvers.py \
      --ids "Fine Tune Run 2/splits/canonical_build_ids.txt" \
      --puzzle-dir "Fine Tune Run 2/puzzles" --model gpt-5 \
      --limit 10 --repair-tries 3        # PILOT first; drop --limit for full run

Accepted -> research/canonical_solvers/<pid>.json   (pid, code, audit, tries)
Report   -> reports/canonical_build_report.json
"""
import argparse, ast, glob, json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from validate_solver import load_puzzle  # noqa

# ---- canonical-shape exemplars (generic, no puzzle leakage) -----------------
EXEMPLARS = '''Example of the REQUIRED shape (reflect-type rule):
```python
def solve(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    def infer_T(g):
        T = [[None]*W for _ in range(H)]
        for r in range(H):
            for c in range(W):
                mirror = g[r][W-1-c]
                if mirror != g[r][c]:
                    T[r][c] = mirror
        return T
    def apply_T(g, T):
        out = [row[:] for row in g]
        for r in range(H):
            for c in range(W):
                if T[r][c] is not None:
                    out[r][c] = T[r][c]
        return out
    return apply_T(input_grid, infer_T(input_grid))
```

Example of the REQUIRED shape (marker/region/boundary rule — this one was
verified to generalize from 3 shown pairs to a hidden 4th grid):
```python
def solve(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    counts = {}
    for row in input_grid:
        for v in row: counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    start = next(((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6), None)
    if start is None: return out
    # infer region reachable from the marker through background
    reachable, stack = set(), [start]
    while stack:
        r, c = stack.pop()
        if (r, c) in reachable or not (0 <= r < H and 0 <= c < W): continue
        if input_grid[r][c] not in (bg, 6): continue
        reachable.add((r, c))
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)): stack.append((r+dr, c+dc))
    # build latent T: reachable background cells on the region boundary -> 7
    T = [[None]*W for _ in range(H)]
    for r, c in reachable:
        if input_grid[r][c] != bg: continue
        if any(not (0<=r+dr<H and 0<=c+dc<W) or (r+dr,c+dc) not in reachable
               for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0)):
            T[r][c] = 7
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None: out[r][c] = T[r][c]
    return out
```'''

SYSTEM = (
    "You are an expert ARC solver. Given a puzzle's training input/output pairs "
    "and the explicit per-cell change mask T (T[r][c]='.' means unchanged, else "
    "the new color), infer the SINGLE invariant rule and write ONE Python "
    "`def solve(input_grid):`.\n\n"
    "HARD REQUIREMENTS:\n"
    "- Canonical shape: solve must INFER a latent transformation mask/T from the "
    "input structure, then APPLY it. Use the form `T = infer_T(grid); return "
    "apply_T(grid, T)` (T may be a 2D None/int mask, a changed-cells dict, a "
    "boundary/fill/repair mask — but it must be an explicit intermediate).\n"
    "- Compute everything from input_grid alone (objects, regions, symmetry, "
    "repetition, components, markers). solve() never sees the output.\n"
    "- NO hardcoded grids, NO `if input_grid == ...`, NO fingerprint/lookup over "
    "examples, NO memorized outputs. Same-size: return same shape as input.\n"
    "- Standard library only. Return ONLY one ```python code block.\n\n"
    + EXEMPLARS
)

def gstr(g): return "\n".join(" ".join(str(c) for c in row) for row in g)
def tstr(inp, out):
    return "\n".join(" ".join("." if inp[r][c]==out[r][c] else str(out[r][c])
                              for c in range(len(inp[0]))) for r in range(len(inp)))

def build_prompt(pz):
    parts = []
    for i, p in enumerate(pz["train"]):
        parts.append(f"PAIR {i+1}\nINPUT:\n{gstr(p['input'])}\nOUTPUT:\n{gstr(p['output'])}\nT:\n{tstr(p['input'],p['output'])}")
    return "\n\n".join(parts) + "\n\nWrite def solve(input_grid): in canonical infer_T/apply_T form. Code only."

CODE = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.DOTALL)
def extract(t):
    m = CODE.findall(t or "")
    if m: return m[-1]
    return t[t.index("def solve"):] if t and "def solve" in t else None

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
    except Exception as e: res.append({"__e__":f"{type(e).__name__}: {e}"})
print(json.dumps({"res":res}))
'''
def run_all(code, pz):
    pairs = pz["train"]+pz["test"]
    ins=[p["input"] for p in pairs]; exps=[p["output"] for p in pairs]
    try:
        r=subprocess.run([sys.executable,"-c",VRUN,json.dumps(ins)],input=code,capture_output=True,text=True,timeout=25)
        out=json.loads(r.stdout.splitlines()[-1]) if r.stdout.strip() else {"err":"no stdout"}
    except subprocess.TimeoutExpired: return None,"timeout",None
    if out.get("err"): return None,out["err"],None
    res=out["res"]
    fails=[]
    for i,(g,e) in enumerate(zip(res,exps)):
        ok=isinstance(g,list) and g and isinstance(g[0],list) and g==e
        if not ok: fails.append((i,g,e))
    return (len(fails)==0), None, fails

def audit(code):
    """Reject hardcoding; require a visible transformation mask. Returns (ok, flags)."""
    flags=[]
    try: t=ast.parse(code)
    except: return False,["unparseable"]
    def gl(n):
        if not isinstance(n,ast.List): return 0
        s=0
        for e in n.elts:
            if isinstance(e,ast.List): s+=len(e.elts)
            else: return 0
        return s
    big=0; eqgrid=False; reads=False
    for n in ast.walk(t):
        big=max(big,gl(n))
        if isinstance(n,ast.Compare):
            for op,c in zip(n.ops,n.comparators):
                if isinstance(op,(ast.Eq,ast.NotEq)) and gl(c)>=9: eqgrid=True
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Subscript): reads=True
    if big>=12: flags.append(f"BIG_GRID_LITERAL({big})")
    if eqgrid: flags.append("EQ_GRID_LOOKUP")
    if "frozenset(" in code and ("known" in code.lower() or "case" in code.lower()): flags.append("FINGERPRINT_LOOKUP")
    has_mask = bool(re.search(r"\b(infer_T|apply_T|mask|delta|changes|boundary|T\s*=)\b", code))
    if not has_mask: flags.append("NO_VISIBLE_MASK")
    hard_reject = any(f.startswith(("BIG_GRID_LITERAL","EQ_GRID_LOOKUP","FINGERPRINT_LOOKUP","unparseable")) for f in flags)
    return (not hard_reject) and has_mask, flags

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ids", default="Fine Tune Run 2/splits/golden_train_ids.txt")
    ap.add_argument("--puzzle-dir", default="Fine Tune Run 2/puzzles")
    ap.add_argument("--model", default="gpt-5")
    ap.add_argument("--repair-tries", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--limit", type=int, default=0)
    args=ap.parse_args()
    from openai import OpenAI
    client=OpenAI()

    def resolve(pid):
        for suf in ("_A2E","_A2T","_A1E","_A1T",""):
            c=Path(args.puzzle_dir)/f"{pid}{suf}.json"
            if c.exists(): return str(c)
        g=glob.glob(f"{args.puzzle_dir}/{pid}*.json"); return g[0] if g else None

    ids=[x.strip() for x in Path(args.ids).read_text().split() if x.strip()]
    if args.limit: ids=ids[:args.limit]
    outdir=ROOT/"research/canonical_solvers"; outdir.mkdir(parents=True, exist_ok=True)
    stats={"attempted":0,"accepted":0,"failed_validate":0,"failed_audit":0,"no_code":0,"solved_on_try":{}}

    for pid in ids:
        f=resolve(pid)
        if not f: continue
        pz=load_puzzle(f); stats["attempted"]+=1
        msgs=[{"role":"system","content":SYSTEM},{"role":"user","content":build_prompt(pz)}]
        accepted=None
        for tryi in range(1, args.repair_tries+1):
            try:
                resp=client.chat.completions.create(model=args.model,temperature=args.temperature,messages=msgs).choices[0].message.content
            except Exception as e:
                print(f"{pid} try{tryi}: API error {e}"); break
            code=extract(resp)
            if not code:
                msgs += [{"role":"assistant","content":resp},{"role":"user","content":"Return ONLY a python code block with def solve(input_grid)."}]; continue
            ok,err,fails=run_all(code,pz)
            if ok:
                aok,flags=audit(code)
                if aok:
                    accepted={"puzzle_id":pid,"code":code,"audit":flags,"tries":tryi}
                    stats["solved_on_try"][str(tryi)]=stats["solved_on_try"].get(str(tryi),0)+1
                    print(f"{pid}: ACCEPTED on try {tryi}  flags={flags}")
                else:
                    print(f"{pid} try{tryi}: passed pairs but FAILED AUDIT {flags}")
                    msgs += [{"role":"assistant","content":resp},{"role":"user","content":f"Rejected: {flags}. Rewrite in canonical infer_T/apply_T form, no hardcoding, expose the mask. Code only."}]
                    continue
                break
            # repair: feed back first failing pair
            if fails:
                i,g,e=fails[0]
                fb=f"Your solve() is wrong on pair {i+1}.\nExpected:\n{gstr(e)}\nGot:\n{gstr(g) if isinstance(g,list) and g and isinstance(g[0],list) else g}\nFix infer_T and return corrected code only."
            else:
                fb=f"Your code errored: {err}. Fix and return code only."
            msgs += [{"role":"assistant","content":resp},{"role":"user","content":fb}]
        if accepted:
            (outdir/f"{pid}.json").write_text(json.dumps(accepted,indent=2)); stats["accepted"]+=1
        else:
            stats["failed_validate"]+=1

    Path(ROOT/"reports").mkdir(exist_ok=True)
    (ROOT/"reports/canonical_build_report.json").write_text(json.dumps(stats,indent=2))
    print("\n=== REPORT ===")
    print(json.dumps(stats,indent=2))
    print(f"accepted canonical solvers -> {outdir}")

if __name__=="__main__":
    main()
