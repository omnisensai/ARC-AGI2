"""
Bulk-collect ARC solve attempts from an LLM via OpenRouter.

Reads splits/<split>.json -> list of puzzle IDs. For each puzzle, runs the
model N times single-shot, extracts code, validates by executing on every
training + test pair, and saves per-run JSON + an aggregate summary.

Usage:
    python bulk_collect.py                          # defaults: raw, 10 runs, Qwen-2.5-7B
    python bulk_collect.py --runs 3 --workers 10    # faster smoke test
    python bulk_collect.py --model openai/gpt-4o-mini

Output:
    bulk_collect_runs/<ts>_<mode>/
        run_meta.json                  config + puzzle list
        <puzzle_id>/run_<NN>.json      per-run record (response, code, pair results, bucket)
        summary.json                   per-puzzle and overall counts
"""

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests


# --- key loading ---

def load_key():
    env = Path("keys.env")
    if not env.exists():
        sys.exit("keys.env missing - copy keys.env.example and fill in OPENROUTER_API_KEY")
    for line in env.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            v = line.split("=", 1)[1].strip()
            if v and not v.startswith("your-"):
                return v
    sys.exit("OPENROUTER_API_KEY not set in keys.env")


# --- prompt ---

def format_grid(grid):
    return "\n".join(" ".join(str(c) for c in row) for row in grid)


def build_seed_prompt(puzzle):
    pairs = []
    for i, p in enumerate(puzzle["train"]):
        pairs.append(
            f"Training pair {i + 1}:\n"
            f"Input:\n{format_grid(p['input'])}\n"
            f"Output:\n{format_grid(p['output'])}"
        )
    test_input = puzzle["test"][0]["input"]
    return (
        "Solve this ARC-AGI puzzle. Identify the transformation rule from the "
        "training pairs and write a Python `def solve(input_grid):` function "
        "that generalizes to all training pairs and the test input.\n\n"
        + "\n\n".join(pairs)
        + f"\n\nTest input:\n{format_grid(test_input)}\n\n"
        "Write ONE `def solve(input_grid):` function. `input_grid` is a list of "
        "lists of ints. Return the output grid as a list of lists of ints.\n\n"
        "Put the final code in a ```python ... ``` block."
    )


# --- code extraction ---

CODE_FENCE_PY = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
CODE_FENCE_ANY = re.compile(r"```\s*\n(.*?)\n```", re.DOTALL)


def extract_code(text):
    m = CODE_FENCE_PY.findall(text)
    if m:
        return m[-1]
    m = CODE_FENCE_ANY.findall(text)
    if m:
        return m[-1]
    if "def solve" in text:
        return text[text.index("def solve"):]
    return None


# --- validation: run code in a subprocess against all train+test pairs ---

VALIDATOR_RUNNER = r'''
import json, sys, traceback
code = sys.stdin.read()
inputs = json.loads(sys.argv[1])
ns = {}
try:
    exec(code, ns)
except Exception as e:
    print(json.dumps({"error": f"exec failed: {type(e).__name__}: {e}",
                      "trace": traceback.format_exc()}))
    sys.exit(0)
fn = ns.get("solve")
if fn is None:
    print(json.dumps({"error": "no solve() function defined"}))
    sys.exit(0)
out = []
for inp in inputs:
    try:
        o = fn(inp)
        if hasattr(o, "tolist"):
            o = o.tolist()
        out.append({"output": o, "error": None})
    except Exception as e:
        out.append({"output": None, "error": f"{type(e).__name__}: {e}"})
print(json.dumps({"results": out, "error": None}))
'''


def compare(got, expected):
    if not isinstance(got, list) or not got:
        return False, None
    if len(got) != len(expected):
        return False, None
    if not isinstance(got[0], list):
        return False, None
    if len(got[0]) != len(expected[0]):
        return False, None
    diff = 0
    for r in range(len(got)):
        if len(got[r]) != len(expected[r]):
            return False, None
        for c in range(len(got[r])):
            if got[r][c] != expected[r][c]:
                diff += 1
    return diff == 0, diff


def validate(code, puzzle, timeout=20):
    inputs = [p["input"] for p in puzzle["train"]] + [p["input"] for p in puzzle["test"]]
    expecteds = [p["output"] for p in puzzle["train"]] + [p["output"] for p in puzzle["test"]]
    pair_types = ["train"] * len(puzzle["train"]) + ["test"] * len(puzzle["test"])

    try:
        proc = subprocess.run(
            [sys.executable, "-c", VALIDATOR_RUNNER, json.dumps(inputs)],
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"exec_error": f"timeout after {timeout}s", "pairs": []}

    stdout = proc.stdout.strip()
    if not stdout:
        return {"exec_error": f"no stdout (stderr: {proc.stderr[:200]})", "pairs": []}
    try:
        out = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError as e:
        return {"exec_error": f"runner output not JSON: {e}", "pairs": []}

    if out.get("error"):
        return {"exec_error": out["error"], "pairs": []}

    pair_results = []
    for i, (got, exp, pt) in enumerate(zip(out["results"], expecteds, pair_types)):
        if got["error"]:
            pair_results.append(
                {"type": pt, "idx": i, "passed": False, "cell_diff": None, "error": got["error"]}
            )
            continue
        passed, diff = compare(got["output"], exp)
        pair_results.append(
            {"type": pt, "idx": i, "passed": passed, "cell_diff": diff, "error": None}
        )
    return {"exec_error": None, "pairs": pair_results}


def classify(pair_results, exec_error):
    if exec_error:
        return "exec_error"
    train = [r for r in pair_results if r["type"] == "train"]
    test = [r for r in pair_results if r["type"] == "test"]
    if not train or not test:
        return "exec_error"
    train_pass = all(r["passed"] for r in train)
    test_pass = all(r["passed"] for r in test)
    if train_pass and test_pass:
        return "correct"
    if train_pass and not test_pass:
        return "wrong_test"
    return "wrong_training"


# --- API call ---

def call_openrouter(api_key, model, prompt, temperature, max_retries=3):
    last = None
    for attempt in range(max_retries):
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
                timeout=180,
            )
            if r.status_code == 429 or r.status_code >= 500:
                last = f"http {r.status_code}: {r.text[:200]}"
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            d = r.json()
            return {
                "text": d["choices"][0]["message"]["content"],
                "usage": d.get("usage"),
            }
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    raise RuntimeError(f"openrouter failed after {max_retries} retries: {last}")


# --- one task ---

def run_one(api_key, model, puzzle_id, puzzle, run_idx, out_dir, temperature):
    prompt = build_seed_prompt(puzzle)
    rec = {"puzzle_id": puzzle_id, "run_idx": run_idx, "model": model,
           "temperature": temperature, "ts": datetime.now().isoformat()}
    try:
        resp = call_openrouter(api_key, model, prompt, temperature)
    except Exception as e:
        rec["bucket"] = "api_error"
        rec["error"] = str(e)
    else:
        rec["response"] = resp["text"]
        rec["usage"] = resp.get("usage")
        code = extract_code(resp["text"])
        rec["code"] = code
        if code is None:
            rec["bucket"] = "no_code"
        else:
            val = validate(code, puzzle)
            rec["pairs"] = val["pairs"]
            rec["exec_error"] = val["exec_error"]
            rec["bucket"] = classify(val["pairs"], val["exec_error"])

    pdir = out_dir / puzzle_id
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / f"run_{run_idx:02d}.json").write_text(json.dumps(rec, indent=2))
    return rec


# --- driver ---

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen/qwen-2.5-7b-instruct")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--splits", default="splits/baseline_10.json")
    ap.add_argument("--puzzle-dir", default="data/training")
    ap.add_argument("--mode", default="raw", choices=["raw"])
    args = ap.parse_args()

    api_key = load_key()
    puzzle_ids = json.loads(Path(args.splits).read_text())["puzzle_ids"]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"bulk_collect_runs/{ts}_{args.mode}")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "run_meta.json").write_text(json.dumps({
        "timestamp": ts, "mode": args.mode, "model": args.model,
        "runs_per_puzzle": args.runs, "temperature": args.temperature,
        "workers": args.workers, "splits": args.splits, "puzzle_ids": puzzle_ids,
    }, indent=2))

    tasks = []
    for pid in puzzle_ids:
        puzzle = json.loads(Path(args.puzzle_dir, f"{pid}.json").read_text())
        for run_idx in range(args.runs):
            tasks.append((pid, puzzle, run_idx))

    print(f"[{ts}] {len(puzzle_ids)} puzzles x {args.runs} runs = {len(tasks)} tasks, "
          f"{args.workers} workers, model={args.model}")
    print(f"out: {out_dir}\n")

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(run_one, api_key, args.model, pid, puzzle, run_idx, out_dir, args.temperature):
            (pid, run_idx)
            for pid, puzzle, run_idx in tasks
        }
        done = 0
        for fut in as_completed(futs):
            pid, run_idx = futs[fut]
            done += 1
            try:
                r = fut.result()
                results.append(r)
                bucket = r.get("bucket", "?")
                tag = "CORRECT" if bucket == "correct" else bucket
                print(f"  [{done:3d}/{len(tasks)}] {pid} run_{run_idx:02d} -> {tag}")
            except Exception as e:
                print(f"  [{done:3d}/{len(tasks)}] {pid} run_{run_idx:02d} -> EXCEPTION: {e}")

    elapsed = time.time() - t0

    # --- summary ---
    per = {}
    for pid in puzzle_ids:
        runs = [r for r in results if r.get("puzzle_id") == pid]
        b = [r.get("bucket", "?") for r in runs]
        per[pid] = {
            "correct": b.count("correct"),
            "wrong_test": b.count("wrong_test"),
            "wrong_training": b.count("wrong_training"),
            "no_code": b.count("no_code"),
            "exec_error": b.count("exec_error"),
            "api_error": b.count("api_error"),
            "total": len(runs),
        }
    total_correct = sum(s["correct"] for s in per.values())
    total_runs = sum(s["total"] for s in per.values()) or 1
    summary = {
        "meta": {"timestamp": ts, "mode": args.mode, "model": args.model,
                 "runs_per_puzzle": args.runs, "elapsed_sec": round(elapsed, 1)},
        "per_puzzle": per,
        "overall": {
            "total_runs": total_runs,
            "correct": total_correct,
            "pass_at_1_avg": round(total_correct / total_runs, 4),
            "puzzles_with_any_correct": sum(1 for s in per.values() if s["correct"] > 0),
            "puzzles_total": len(puzzle_ids),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== SUMMARY ===")
    print(f"  elapsed: {elapsed:.1f}s")
    print(f"  total runs: {total_runs}")
    print(f"  correct: {total_correct} ({100 * total_correct / total_runs:.1f}% pass@1 avg)")
    print(f"  puzzles solved >=1x: {summary['overall']['puzzles_with_any_correct']} / {len(puzzle_ids)}")
    print(f"\n  -> {out_dir}/summary.json")


if __name__ == "__main__":
    main()
