"""Run locked arc2_eval against vLLM-served LoRA. Matches training prompt exactly.

Usage:
    # Smoke test on 3 puzzles
    python run_eval_lora.py --limit 3

    # Full 120 puzzles, 2 attempts each
    python run_eval_lora.py

    # Compare against base Qwen (no LoRA)
    python run_eval_lora.py --model Qwen/Qwen2.5-7B-Instruct

Companion to research/case_studies/arc_lora_run1_locked_eval.md
"""
import argparse, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import requests

from substrate import format_grid  # compact: no spaces, no commas


SYSTEM_TAG = "D"  # phase2: puzzle -> code


def build_user_prompt(puzzle):
    parts = []
    for i, p in enumerate(puzzle["train"]):
        parts.append(
            f"Training pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
            f"Output:\n{format_grid(p['output'])}"
        )
    for i, p in enumerate(puzzle["test"]):
        parts.append(f"Test input:\n{format_grid(p['input'])}")
    return (
        "Write a Python `def solve(input_grid):` function that produces the "
        "correct output for the test input. The function must generalize from "
        "the training pairs below.\n\n" + "\n\n".join(parts)
    )


CODE_PY = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
CODE_ANY = re.compile(r"```\s*\n(.*?)\n```", re.DOTALL)

def extract_code(text):
    for rx in (CODE_PY, CODE_ANY):
        m = rx.findall(text)
        if m: return m[-1]
    if "def solve" in text:
        return text[text.index("def solve"):]
    return None


VRUN = r'''
import json,sys,traceback
code=sys.stdin.read(); inputs=json.loads(sys.argv[1]); ns={}
try: exec(code, ns)
except Exception as e:
    print(json.dumps({"error": f"exec failed: {type(e).__name__}: {e}"})); sys.exit(0)
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

def grids_eq(a, b):
    if not isinstance(a, list) or not a or not isinstance(a[0], list): return False
    if len(a) != len(b) or any(len(ar) != len(br) for ar, br in zip(a, b)): return False
    return all(a[r][c] == b[r][c] for r in range(len(a)) for c in range(len(a[r])))


def validate(code, puzzle, timeout=20):
    inputs = [p["input"] for p in puzzle["train"]] + [p["input"] for p in puzzle["test"]]
    exps   = [p["output"] for p in puzzle["train"]] + [p["output"] for p in puzzle["test"]]
    n_train = len(puzzle["train"])
    try:
        r = subprocess.run([sys.executable, "-c", VRUN, json.dumps(inputs)],
                           input=code, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"exec_error": "timeout", "train_pass": False, "test_pass": False}
    if not r.stdout.strip():
        return {"exec_error": f"no stdout: {r.stderr[:200]}", "train_pass": False, "test_pass": False}
    out = json.loads(r.stdout.splitlines()[-1])
    if out.get("error"):
        return {"exec_error": out["error"], "train_pass": False, "test_pass": False}
    pair_ok = [g["error"] is None and grids_eq(g["output"], e) for g, e in zip(out["results"], exps)]
    return {"exec_error": None,
            "train_pass": all(pair_ok[:n_train]),
            "test_pass": all(pair_ok[n_train:])}


def call_vllm(base, model, system, user, temperature, max_tokens):
    r = requests.post(f"{base.rstrip('/')}/chat/completions",
        headers={"Authorization": "Bearer EMPTY", "Content-Type": "application/json"},
        json={"model": model,
              "messages": [{"role":"system","content":system},{"role":"user","content":user}],
              "temperature": temperature, "max_tokens": max_tokens, "top_p": 0.95},
        timeout=600)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def run_one(args, pid, puzzle, attempt):
    user = build_user_prompt(puzzle)
    try:
        resp = call_vllm(args.api_base, args.model, SYSTEM_TAG, user,
                         args.temperature, args.max_tokens)
    except Exception as e:
        return {"pid": pid, "attempt": attempt, "bucket": "api_error", "error": str(e)}
    code = extract_code(resp)
    rec = {"pid": pid, "attempt": attempt, "response": resp, "code": code}
    if code is None:
        rec["bucket"] = "no_code"; return rec
    v = validate(code, puzzle)
    rec.update(v)
    if v["exec_error"]: rec["bucket"] = "exec_error"
    elif v["test_pass"] and v["train_pass"]: rec["bucket"] = "correct"
    elif v["train_pass"]: rec["bucket"] = "wrong_test"
    else: rec["bucket"] = "wrong_training"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="arc", help="vLLM model id; 'arc' = LoRA, 'Qwen/Qwen2.5-7B-Instruct' = base")
    ap.add_argument("--splits", default="splits/locked_arc2_eval.json")
    ap.add_argument("--puzzle-dir", default="data/arc2_eval")
    ap.add_argument("--attempts", type=int, default=2, help="ARC-AGI-2 scores pass@2")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    pids = json.loads(Path(args.splits).read_text())["puzzle_ids"]
    if args.limit: pids = pids[:args.limit]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(f"eval_runs/{ts}_{args.model.replace('/','_')}")
    out.mkdir(parents=True, exist_ok=True)

    puzzles = {}
    missing = []
    for pid in pids:
        f = Path(args.puzzle_dir) / f"{pid}.json"
        if not f.exists():
            missing.append(pid); continue
        puzzles[pid] = json.loads(f.read_text())
    if missing:
        print(f"MISSING {len(missing)} puzzles (first 5: {missing[:5]}). Fix --puzzle-dir.")
        if not puzzles: sys.exit(1)

    tasks = [(pid, puzzles[pid], a) for pid in puzzles for a in range(args.attempts)]
    print(f"{len(puzzles)} puzzles x {args.attempts} attempts = {len(tasks)} calls, model={args.model}")

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, args, pid, p, a): (pid, a) for pid, p, a in tasks}
        done = 0
        for fut in as_completed(futs):
            pid, a = futs[fut]; done += 1
            r = fut.result()
            (out / f"{pid}__a{a}.json").write_text(json.dumps(r, indent=2))
            results.append(r)
            print(f"  [{done:3d}/{len(tasks)}] {pid} a{a} -> {r.get('bucket')}")

    # pass@k
    by_pid = {}
    for r in results: by_pid.setdefault(r["pid"], []).append(r)
    pass1 = sum(1 for rs in by_pid.values() if any(x.get("bucket")=="correct" and x.get("attempt")==0 for x in rs))
    pass2 = sum(1 for rs in by_pid.values() if any(x.get("bucket") == "correct" for x in rs))
    solved_ids = sorted(pid for pid, rs in by_pid.items() if any(x.get("bucket")=="correct" for x in rs))
    summary = {"meta": {"model": args.model, "attempts": args.attempts, "temperature": args.temperature,
                        "n_puzzles": len(by_pid), "elapsed_sec": round(time.time()-t0,1)},
               "pass_at_1": pass1, "pass_at_2": pass2,
               "pct_pass_at_1": round(100*pass1/len(by_pid),2),
               "pct_pass_at_2": round(100*pass2/len(by_pid),2),
               "solved_puzzle_ids": solved_ids}
    (out/"summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"-> {out}/summary.json")

if __name__ == "__main__":
    main()
