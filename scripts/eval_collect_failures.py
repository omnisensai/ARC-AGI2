"""Failure-trace collection for Phase 2 curriculum (Code Contract / Solver / Repair).

Goal is observability, NOT leaderboard score. Saves enough evidence per attempt
to build training data of the form:
    wrong code + factual validator feedback -> corrected code

Spec: research/case_studies/arc_lora_run1_*.md and the GPT spec in chat history.

Output structure:
    eval_runs/<ts>_failure_probe/
        summary.json                # machine-readable rollup
        summary.md                  # human-readable + Phase 2 recommendations
        attempts.jsonl              # one line per attempt (full schema)
        attempts/<pid>_a<n>.json    # pretty per-attempt copy
        code/<pid>_a<n>.py          # extracted code, runnable
        outputs/<pid>_a<n>_train_outputs.json   # actual outputs per train pair

Usage:
    python scripts/eval_collect_failures.py \\
        --model arc \\
        --limit 60 --attempts 2 --temperature 0.7 \\
        --out eval_runs/$(date +%Y%m%d_%H%M%S)_failure_probe
"""
import argparse, ast, hashlib, json, os, re, subprocess, sys, time, traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from substrate import format_grid  # compact grids


SYSTEM_TAG = "D"
ALLOWED_IMPORTS = {"math", "collections", "itertools", "copy", "functools",
                   "operator", "statistics"}
BLOCKED_NAMES = {"os", "sys", "subprocess", "socket", "requests", "pathlib",
                 "shutil", "builtins", "importlib", "ctypes", "multiprocessing",
                 "threading", "asyncio", "pickle", "marshal"}
BLOCKED_CALLS = {"open", "exec", "eval", "__import__", "compile", "input"}


# --------------------------------------------------------------------------
# Prompt construction (must match training distribution)
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# Code extraction + static safety analysis
# --------------------------------------------------------------------------

CODE_PY = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
CODE_ANY = re.compile(r"```\s*\n(.*?)\n```", re.DOTALL)


def extract_code(text):
    for rx in (CODE_PY, CODE_ANY):
        m = rx.findall(text)
        if m:
            return m[-1]
    if "def solve" in text:
        return text[text.index("def solve"):]
    return None


def parse_check(code):
    """Returns (has_code, has_solve, syntax_ok, syntax_error)."""
    if not code:
        return False, False, False, None
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return True, "def solve" in code, False, f"{type(e).__name__}: {e}"
    has_solve = any(isinstance(n, ast.FunctionDef) and n.name == "solve"
                    for n in ast.walk(tree))
    return True, has_solve, True, None


def static_safety_check(code):
    """Return error string if code uses blocked features, None otherwise."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # syntax_error bucket handles this
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                root = n.name.split(".")[0]
                if root in BLOCKED_NAMES:
                    return f"BlockedImport: {n.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in BLOCKED_NAMES:
                return f"BlockedImport: from {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                return f"BlockedCall: {node.func.id}"
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in {"system", "popen", "spawn", "Popen"}:
                    return f"BlockedAttrCall: .{node.func.attr}"
    return None


# --------------------------------------------------------------------------
# Sandboxed execution: one subprocess call runs solve() on every input,
# subprocess itself enforces a hard timeout. signal.alarm() inside the
# runner gives per-call protection too.
# --------------------------------------------------------------------------

RUNNER = r'''
import json, sys, signal, traceback

TIMEOUT = float(sys.argv[2])

def _on_alarm(signum, frame):
    raise TimeoutError("solve() exceeded per-pair timeout")

signal.signal(signal.SIGALRM, _on_alarm)

code = sys.stdin.read()
inputs = json.loads(sys.argv[1])
ns = {}
try:
    exec(code, ns)
except Exception as e:
    print(json.dumps({"phase":"exec",
                      "exception_type": type(e).__name__,
                      "exception_message": str(e),
                      "traceback": traceback.format_exc()}))
    sys.exit(0)

fn = ns.get("solve")
if not callable(fn):
    print(json.dumps({"phase":"contract",
                      "exception_type":"NoSolveFunction",
                      "exception_message":"solve not defined or not callable"}))
    sys.exit(0)

results = []
for inp in inputs:
    signal.alarm(int(TIMEOUT) + 1)
    t0 = __import__("time").perf_counter()
    try:
        out = fn(inp)
        if hasattr(out, "tolist"):
            out = out.tolist()
        results.append({
            "status": "ok",
            "output": out,
            "runtime_ms": round((__import__("time").perf_counter() - t0) * 1000, 2),
            "exception_type": None,
            "exception_message": None,
            "traceback": None,
        })
    except TimeoutError as e:
        results.append({"status":"timeout","output":None,"runtime_ms":None,
                        "exception_type":"TimeoutError","exception_message":str(e),
                        "traceback":None})
    except Exception as e:
        results.append({"status":"exec_error","output":None,"runtime_ms":None,
                        "exception_type":type(e).__name__,
                        "exception_message":str(e),
                        "traceback":traceback.format_exc()})
    finally:
        signal.alarm(0)

print(json.dumps({"phase":"done","results":results}))
'''


def run_code_on_inputs(code, inputs, timeout_per_pair=2.0, hard_timeout=30.0):
    """Execute code in subprocess; run solve() on each input."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER, json.dumps(inputs), str(timeout_per_pair)],
            input=code, capture_output=True, text=True, timeout=hard_timeout)
    except subprocess.TimeoutExpired:
        return {"phase": "hard_timeout", "exception_type": "TimeoutError",
                "exception_message": f"subprocess exceeded {hard_timeout}s"}
    out = proc.stdout.strip()
    if not out:
        return {"phase": "no_stdout", "exception_type": "NoStdout",
                "exception_message": (proc.stderr or "")[:300]}
    try:
        return json.loads(out.splitlines()[-1])
    except json.JSONDecodeError:
        return {"phase": "bad_json", "exception_type": "BadRunnerJSON",
                "exception_message": out[-300:]}


# --------------------------------------------------------------------------
# Grid contract + diff
# --------------------------------------------------------------------------

def inspect_grid(obj):
    info = {"returned_type": type(obj).__name__,
            "is_grid": False, "is_rectangular": False,
            "height": None, "width": None,
            "all_int": False, "all_cells_0_9": False}
    if not isinstance(obj, list) or not obj:
        return info
    if not all(isinstance(r, list) for r in obj):
        return info
    if any(len(r) == 0 for r in obj):
        return info
    w = len(obj[0])
    info["is_grid"] = True
    info["height"] = len(obj)
    info["width"] = w
    info["is_rectangular"] = all(len(r) == w for r in obj)
    if not info["is_rectangular"]:
        return info
    all_int = True
    all_09 = True
    for r in obj:
        for c in r:
            if not isinstance(c, int) or isinstance(c, bool):
                all_int = False; all_09 = False; break
            if not (0 <= c <= 9):
                all_09 = False
        if not all_int:
            break
    info["all_int"] = all_int
    info["all_cells_0_9"] = all_09
    return info


def diff_map(actual, expected):
    """Return ASCII diff: . = match, X = wrong. None if shape mismatch."""
    if not isinstance(actual, list) or not actual or not isinstance(actual[0], list):
        return None
    if len(actual) != len(expected):
        return None
    if any(len(a) != len(e) for a, e in zip(actual, expected)):
        return None
    return ["".join("." if a == e else "X" for a, e in zip(arow, erow))
            for arow, erow in zip(actual, expected)]


def cell_diff_count(actual, expected):
    if not isinstance(actual, list) or not actual or not isinstance(actual[0], list):
        return None
    if len(actual) != len(expected) or any(len(a) != len(e) for a, e in zip(actual, expected)):
        return None
    diffs = sum(1 for r in range(len(expected))
                  for c in range(len(expected[0])) if actual[r][c] != expected[r][c])
    return diffs


# --------------------------------------------------------------------------
# Bucket classification (order matters, per spec)
# --------------------------------------------------------------------------

def classify(rec):
    p = rec["parse"]
    if not p["has_code"]:
        return "no_code"
    if not p["syntax_ok"]:
        return "syntax_error"
    ex = rec["execution"]
    if ex["status"] == "timeout":
        return "timeout"
    if ex["status"] in ("exec_error", "invalid_return"):
        return "exec_error"

    rc = rec["return_contract"]
    if not rc["is_grid"]:
        return "train_no_grid"
    if not rc["is_rectangular"]:
        return "non_rectangular"
    if not (rc["all_int"] and rc["all_cells_0_9"]):
        return "bad_cell_values"

    train = rec["train_results"]
    if any(t["status"] == "wrong_shape" for t in train):
        return "wrong_shape"
    if all(t["status"] == "pass" for t in train):
        return "correct"

    avg = rec["aggregate"]["avg_train_cell_accuracy"]
    if avg is not None and avg >= 0.95:
        return "near_miss_95"
    if avg is not None and avg >= 0.90:
        return "near_miss_90"
    return "wrong_training"


# --------------------------------------------------------------------------
# vLLM client
# --------------------------------------------------------------------------

def call_vllm(base, model, system, user, temperature, max_tokens):
    r = requests.post(f"{base.rstrip('/')}/chat/completions",
        headers={"Authorization": "Bearer EMPTY", "Content-Type": "application/json"},
        json={"model": model,
              "messages": [{"role":"system","content":system},
                           {"role":"user","content":user}],
              "temperature": temperature, "max_tokens": max_tokens,
              "top_p": 0.95},
        timeout=600)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------
# Per-attempt pipeline
# --------------------------------------------------------------------------

def process_attempt(args, pid, puzzle, attempt_idx, out_dir):
    started = datetime.now(timezone.utc).isoformat()
    prompt = build_user_prompt(puzzle)
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()[:16]

    rec = {
        "puzzle_id": pid,
        "attempt_id": attempt_idx,
        "source": args.source,
        "timestamp": started,
        "model": args.model,
        "temperature": args.temperature,
        "prompt_sha256": prompt_sha,
        "code_sha256": None,
        "shapes": {
            "train": [
                {"pair_index": i,
                 "input_shape": [len(p["input"]), len(p["input"][0])],
                 "expected_output_shape": [len(p["output"]), len(p["output"][0])]}
                for i, p in enumerate(puzzle["train"])
            ],
            "test_input_shape": [len(puzzle["test"][0]["input"]),
                                 len(puzzle["test"][0]["input"][0])],
            "known_test_output_shape": (
                [len(puzzle["test"][0]["output"]), len(puzzle["test"][0]["output"][0])]
                if "output" in puzzle["test"][0] else None
            ),
        },
        "prompt": prompt,
        "generated_text": None,
        "extracted_code": None,
        "parse": {"has_code": False, "has_solve_function": False,
                  "syntax_ok": False, "syntax_error": None},
        "execution": {"status": None, "exception_type": None,
                      "exception_message": None, "traceback": None,
                      "runtime_ms_total": None},
        "return_contract": {"returned_type": None, "is_grid": False,
                            "is_rectangular": False, "height": None,
                            "width": None, "all_int": False,
                            "all_cells_0_9": False},
        "train_results": [],
        "aggregate": {"all_train_pass": False,
                      "avg_train_cell_accuracy": None,
                      "min_train_cell_accuracy": None,
                      "max_train_cell_accuracy": None,
                      "total_cell_diff": None,
                      "total_cells": None,
                      "shape_correct_all_train": False,
                      "near_miss_95": False,
                      "near_miss_90": False},
        "failure_bucket": None,
    }

    # 1) Generate
    try:
        resp = call_vllm(args.api_base, args.model, SYSTEM_TAG, prompt,
                         args.temperature, args.max_tokens)
        rec["generated_text"] = resp
    except Exception as e:
        rec["execution"]["status"] = "exec_error"
        rec["execution"]["exception_type"] = "APIError"
        rec["execution"]["exception_message"] = str(e)
        rec["failure_bucket"] = "exec_error"
        return rec

    # 2) Extract + parse
    code = extract_code(resp)
    rec["extracted_code"] = code
    if code is not None:
        rec["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()[:16]
        (out_dir / "code" / f"{pid}_a{attempt_idx}.py").write_text(code)
    has_code, has_solve, syntax_ok, syntax_err = parse_check(code)
    rec["parse"] = {"has_code": has_code, "has_solve_function": has_solve,
                    "syntax_ok": syntax_ok, "syntax_error": syntax_err}
    if not has_code:
        rec["execution"]["status"] = "no_code"
        rec["failure_bucket"] = "no_code"
        return rec
    if not syntax_ok:
        rec["execution"]["status"] = "syntax_error"
        rec["execution"]["exception_type"] = "SyntaxError"
        rec["execution"]["exception_message"] = syntax_err
        rec["failure_bucket"] = "syntax_error"
        return rec

    # 3) Static safety
    blocked = static_safety_check(code)
    if blocked:
        rec["execution"]["status"] = "exec_error"
        rec["execution"]["exception_type"] = "BlockedCode"
        rec["execution"]["exception_message"] = blocked
        rec["failure_bucket"] = "exec_error"
        return rec

    # 4) Execute
    inputs = [p["input"] for p in puzzle["train"]]
    t0 = time.perf_counter()
    result = run_code_on_inputs(code, inputs,
                                timeout_per_pair=args.timeout_per_pair,
                                hard_timeout=args.hard_timeout)
    rec["execution"]["runtime_ms_total"] = round((time.perf_counter() - t0) * 1000, 2)

    if result.get("phase") in ("hard_timeout",):
        rec["execution"]["status"] = "timeout"
        rec["execution"]["exception_type"] = result.get("exception_type")
        rec["execution"]["exception_message"] = result.get("exception_message")
        rec["failure_bucket"] = "timeout"
        return rec
    if result.get("phase") == "exec":
        rec["execution"]["status"] = "exec_error"
        rec["execution"]["exception_type"] = result.get("exception_type")
        rec["execution"]["exception_message"] = result.get("exception_message")
        rec["execution"]["traceback"] = result.get("traceback")
        rec["failure_bucket"] = "exec_error"
        return rec
    if result.get("phase") == "contract":
        rec["execution"]["status"] = "exec_error"
        rec["execution"]["exception_type"] = result.get("exception_type")
        rec["execution"]["exception_message"] = result.get("exception_message")
        rec["failure_bucket"] = "exec_error"
        return rec
    if result.get("phase") in ("no_stdout", "bad_json"):
        rec["execution"]["status"] = "exec_error"
        rec["execution"]["exception_type"] = result.get("exception_type")
        rec["execution"]["exception_message"] = result.get("exception_message")
        rec["failure_bucket"] = "exec_error"
        return rec

    # phase == "done"
    pair_results = result["results"]

    # 5) Inspect & score each pair
    actual_outputs = []
    train_table = []
    saw_any_grid = False
    cell_diffs = []
    cell_totals = []
    shape_correct_all = True
    any_timeout = False
    any_exec_error = False

    for i, (pair, run_out) in enumerate(zip(puzzle["train"], pair_results)):
        expected = pair["output"]
        exp_shape = [len(expected), len(expected[0])]
        inp_shape = [len(pair["input"]), len(pair["input"][0])]
        entry = {
            "pair_index": i,
            "status": None,
            "input_shape": inp_shape,
            "expected_shape": exp_shape,
            "actual_shape": None,
            "cell_diff": None,
            "total_cells": exp_shape[0] * exp_shape[1],
            "cell_accuracy": None,
            "diff_map": None,
            "exception_type": run_out.get("exception_type"),
            "exception_message": run_out.get("exception_message"),
            "runtime_ms": run_out.get("runtime_ms"),
        }
        actual_outputs.append({"pair_index": i,
                               "input": pair["input"],
                               "expected": expected,
                               "actual": run_out.get("output"),
                               "error": run_out.get("exception_type")})
        if run_out["status"] == "timeout":
            entry["status"] = "timeout"; any_timeout = True
            train_table.append(entry); continue
        if run_out["status"] == "exec_error":
            entry["status"] = "exec_error"; any_exec_error = True
            train_table.append(entry); continue

        actual = run_out["output"]
        info = inspect_grid(actual)
        if not info["is_grid"]:
            entry["status"] = "invalid_return"
            train_table.append(entry); continue
        saw_any_grid = True
        actual_shape = [info["height"], info["width"]]
        entry["actual_shape"] = actual_shape
        if actual_shape != exp_shape:
            entry["status"] = "wrong_shape"
            shape_correct_all = False
            train_table.append(entry); continue
        # same shape; cell-level scoring
        diffs = cell_diff_count(actual, expected)
        entry["cell_diff"] = diffs
        entry["cell_accuracy"] = round(1 - diffs / entry["total_cells"], 4)
        entry["diff_map"] = diff_map(actual, expected)
        entry["status"] = "pass" if diffs == 0 else "wrong_grid"
        cell_diffs.append(diffs)
        cell_totals.append(entry["total_cells"])
        train_table.append(entry)

    rec["train_results"] = train_table

    # 6) Top-level execution.status
    if any_timeout:
        rec["execution"]["status"] = "timeout"
    elif any_exec_error:
        rec["execution"]["status"] = "exec_error"
    elif not saw_any_grid:
        rec["execution"]["status"] = "invalid_return"
    else:
        rec["execution"]["status"] = "pass"

    # 7) Return contract: take first pair's actual output as the canonical return
    first_actual = pair_results[0].get("output") if pair_results else None
    info0 = inspect_grid(first_actual)
    rec["return_contract"].update(info0)

    # 8) Aggregate
    all_pass = train_table and all(t["status"] == "pass" for t in train_table)
    accs = [t["cell_accuracy"] for t in train_table if t["cell_accuracy"] is not None]
    rec["aggregate"]["all_train_pass"] = all_pass
    rec["aggregate"]["avg_train_cell_accuracy"] = (
        round(sum(accs) / len(accs), 4) if accs else None)
    rec["aggregate"]["min_train_cell_accuracy"] = min(accs) if accs else None
    rec["aggregate"]["max_train_cell_accuracy"] = max(accs) if accs else None
    rec["aggregate"]["total_cell_diff"] = sum(cell_diffs) if cell_diffs else None
    rec["aggregate"]["total_cells"] = sum(cell_totals) if cell_totals else None
    rec["aggregate"]["shape_correct_all_train"] = shape_correct_all
    rec["aggregate"]["near_miss_95"] = bool(
        rec["aggregate"]["avg_train_cell_accuracy"] and
        rec["aggregate"]["avg_train_cell_accuracy"] >= 0.95 and not all_pass)
    rec["aggregate"]["near_miss_90"] = bool(
        rec["aggregate"]["avg_train_cell_accuracy"] and
        rec["aggregate"]["avg_train_cell_accuracy"] >= 0.90 and not all_pass)

    # 9) Bucket
    rec["failure_bucket"] = classify(rec)

    # Save per-pair outputs separately
    (out_dir / "outputs" / f"{pid}_a{attempt_idx}_train_outputs.json").write_text(
        json.dumps(actual_outputs, indent=2))

    return rec


# --------------------------------------------------------------------------
# Summary writers
# --------------------------------------------------------------------------

def shape_type(puzzle):
    """same_size if every train pair preserves shape; diff_size if all change; mixed otherwise."""
    same = []
    for p in puzzle["train"]:
        ih, iw = len(p["input"]), len(p["input"][0])
        oh, ow = len(p["output"]), len(p["output"][0])
        same.append(ih == oh and iw == ow)
    if all(same):
        return "same_size"
    if not any(same):
        return "diff_size"
    return "mixed"


def write_summary(records, out_dir, puzzles_by_pid, meta):
    bucket_counts = Counter(r["failure_bucket"] for r in records)
    by_shape = defaultdict(lambda: Counter())
    for r in records:
        st = shape_type(puzzles_by_pid[r["puzzle_id"]])
        by_shape[st][r["failure_bucket"]] += 1
    exc_counts = Counter(r["execution"]["exception_type"]
                         for r in records
                         if r["execution"]["exception_type"])
    near_miss = sorted(
        [(r["puzzle_id"], r["attempt_id"], r["aggregate"]["avg_train_cell_accuracy"])
         for r in records if r["aggregate"]["avg_train_cell_accuracy"] is not None],
        key=lambda x: -(x[2] or 0))[:20]
    contract_fail = []
    for r in records:
        rc = r["return_contract"]
        if r["failure_bucket"] in ("train_no_grid", "non_rectangular", "bad_cell_values"):
            contract_fail.append({
                "puzzle_id": r["puzzle_id"], "attempt_id": r["attempt_id"],
                "returned_type": rc["returned_type"],
                "is_rectangular": rc["is_rectangular"],
                "all_int": rc["all_int"], "all_cells_0_9": rc["all_cells_0_9"],
            })
    wrong_shape_examples = []
    for r in records:
        if r["failure_bucket"] != "wrong_shape":
            continue
        for t in r["train_results"]:
            if t["status"] == "wrong_shape":
                wrong_shape_examples.append({
                    "puzzle_id": r["puzzle_id"], "attempt_id": r["attempt_id"],
                    "pair_index": t["pair_index"],
                    "expected_shape": t["expected_shape"],
                    "actual_shape": t["actual_shape"],
                })
                break

    summary = {
        "meta": meta,
        "n_attempts": len(records),
        "n_puzzles": len(set(r["puzzle_id"] for r in records)),
        "bucket_counts": dict(bucket_counts),
        "shape_type_breakdown": {k: dict(v) for k, v in by_shape.items()},
        "exception_counts": dict(exc_counts),
        "top_near_misses": [
            {"puzzle_id": p, "attempt_id": a, "avg_train_cell_accuracy": acc}
            for p, a, acc in near_miss if acc and acc < 1.0],
        "contract_failures": contract_fail[:30],
        "wrong_shape_examples": wrong_shape_examples[:30],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    # Markdown
    md = [f"# Failure-probe summary\n",
          f"_{meta['started']}, model `{meta['model']}`, T={meta['temperature']}, "
          f"{summary['n_attempts']} attempts across {summary['n_puzzles']} puzzles_\n",
          "## Bucket counts\n",
          "| Bucket | N |", "|---|---|"]
    for b, n in bucket_counts.most_common():
        md.append(f"| `{b}` | {n} |")
    md.append("\n## Shape-type breakdown\n")
    md.append("| Shape type | " + " | ".join(sorted(bucket_counts)) + " |")
    md.append("|" + "---|" * (len(bucket_counts) + 1))
    for st in ("same_size", "diff_size", "mixed"):
        row = [st]
        for b in sorted(bucket_counts):
            row.append(str(by_shape[st].get(b, 0)))
        md.append("| " + " | ".join(row) + " |")
    md.append("\n## Top near-misses\n")
    md.append("| PID | attempt | avg train cell acc |")
    md.append("|---|---|---|")
    for p, a, acc in near_miss[:15]:
        if acc and acc < 1.0:
            md.append(f"| `{p}` | {a} | {acc:.4f} |")
    md.append("\n## Exception types\n")
    md.append("| Type | N |")
    md.append("|---|---|")
    for t, n in exc_counts.most_common(15):
        md.append(f"| `{t}` | {n} |")
    md.append("\n## Contract failures (first 10)\n")
    for cf in contract_fail[:10]:
        md.append(f"- `{cf['puzzle_id']}` a{cf['attempt_id']}: returned "
                  f"`{cf['returned_type']}`, rect={cf['is_rectangular']}, "
                  f"all_int={cf['all_int']}, 0-9={cf['all_cells_0_9']}")
    md.append("\n## Wrong-shape examples (first 10)\n")
    for w in wrong_shape_examples[:10]:
        md.append(f"- `{w['puzzle_id']}` a{w['attempt_id']} pair {w['pair_index']}: "
                  f"expected {w['expected_shape']}, got {w['actual_shape']}")
    md.append("\n## Phase 2 curriculum recommendation\n")
    md.append(_phase2_reco(bucket_counts, by_shape, exc_counts))
    (out_dir / "summary.md").write_text("\n".join(md))


def _phase2_reco(bucket_counts, by_shape, exc_counts):
    total = sum(bucket_counts.values()) or 1
    parts = []
    ws = bucket_counts.get("wrong_shape", 0) + by_shape.get("diff_size", {}).get("train_no_grid", 0)
    ng = bucket_counts.get("train_no_grid", 0)
    nm = bucket_counts.get("near_miss_95", 0) + bucket_counts.get("near_miss_90", 0)
    ex = bucket_counts.get("exec_error", 0) + bucket_counts.get("syntax_error", 0)

    if ws + by_shape.get("diff_size", {}).get("train_no_grid", 0) > total * 0.15:
        parts.append("- **Code Contract (shape)**: significant `wrong_shape` and "
                     "diff-size `train_no_grid` rate. Highest-leverage move is "
                     "augmenting `phase2_train.jsonl` with explicit output-shape "
                     "computation from training pair dimensions.")
    if ng > total * 0.15:
        parts.append("- **Code Contract (return type)**: many attempts return non-grids. "
                     "Add training records that end with a grid-shape assertion before return.")
    if exc_counts.get("NameError", 0) > 0:
        parts.append("- **Imports**: `NameError` shows in exec failures — likely missing "
                     "`from collections import Counter, deque`. Standardize imports in phase-2 bodies.")
    if nm > 0:
        parts.append(f"- **Code Repair**: {nm} near-miss attempts (≥90% cell acc) are prime "
                     "candidates for the corrector task — pair wrong code + diff-map feedback → right code.")
    if bucket_counts.get("correct", 0) == 0 and nm == 0:
        parts.append("- **Bigger sample**: zero correct AND zero near-miss in this probe; "
                     "extend to full 120 with pass@5+ before concluding the LoRA can't solve any.")
    if not parts:
        parts.append("- Probe too small or too clean to recommend changes.")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="arc")
    ap.add_argument("--splits", default="splits/locked_arc2_eval.json")
    ap.add_argument("--puzzle-dir", default="data/arc2_eval")
    ap.add_argument("--source", default="a2e_dev_hard")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout-per-pair", type=float, default=2.0)
    ap.add_argument("--hard-timeout", type=float, default=30.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("attempts", "code", "outputs"):
        (out_dir / sub).mkdir(exist_ok=True)
    attempts_jsonl = out_dir / "attempts.jsonl"
    attempts_jsonl.write_text("")  # truncate

    pids = json.loads(Path(args.splits).read_text())["puzzle_ids"]
    if args.limit:
        pids = pids[:args.limit]

    puzzles = {}
    missing = []
    for pid in pids:
        f = Path(args.puzzle_dir) / f"{pid}.json"
        if not f.exists():
            missing.append(pid); continue
        puzzles[pid] = json.loads(f.read_text())
    if missing:
        print(f"WARN missing puzzles: {missing[:5]}... ({len(missing)})")
    pids = [p for p in pids if p in puzzles]

    started = datetime.now(timezone.utc).isoformat()
    meta = {"started": started, "model": args.model,
            "temperature": args.temperature, "attempts_per_puzzle": args.attempts,
            "splits": args.splits, "limit": args.limit,
            "timeout_per_pair": args.timeout_per_pair, "workers": args.workers}

    tasks = [(pid, puzzles[pid], a) for pid in pids for a in range(args.attempts)]
    print(f"{len(pids)} puzzles x {args.attempts} attempts = {len(tasks)} tasks, "
          f"model={args.model}, T={args.temperature}, out={out_dir}")

    records = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_attempt, args, pid, p, a, out_dir): (pid, a)
                for pid, p, a in tasks}
        done = 0
        for fut in as_completed(futs):
            pid, a = futs[fut]; done += 1
            try:
                rec = fut.result()
            except Exception as e:
                print(f"  [{done:3d}/{len(tasks)}] {pid} a{a} -> EXCEPTION {e}")
                continue
            # write pretty per-attempt
            (out_dir / "attempts" / f"{pid}_a{a}.json").write_text(
                json.dumps(rec, indent=2))
            # append to JSONL atomically
            with attempts_jsonl.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            records.append(rec)
            print(f"  [{done:3d}/{len(tasks)}] {pid} a{a} -> {rec['failure_bucket']}")

    elapsed = time.time() - t0
    meta["elapsed_sec"] = round(elapsed, 1)
    write_summary(records, out_dir, puzzles, meta)
    print(f"\nDONE in {elapsed:.0f}s")
    print(f"  attempts: {len(records)}")
    print(f"  summary: {out_dir}/summary.json")
    print(f"  summary: {out_dir}/summary.md")


if __name__ == "__main__":
    main()
