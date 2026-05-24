#!/usr/bin/env python3
"""Validate a `def solve(input_grid)` against an ARC puzzle's pairs.

A solver is ACCEPTED only if it reproduces EVERY train AND test pair exactly
(cell-for-cell). Runs the candidate in an isolated subprocess with a wall-clock
timeout so a hang/crash can't take down the caller. This is the single source
of truth used both by the solver-generation agents (to self-check) and by the
orchestrator (to independently re-verify before a solver is committed).

Grids in the puzzle JSON are the compact one-char-per-cell format
("86\\n64"); they are parsed to list[list[int]] before being handed to solve().

Usage (CLI):
    python scripts/validate_solver.py <puzzle.json> <solver.py>
    # prints a JSON result and exits 0 iff overall_pass

Importable:
    from validate_solver import validate_code
    result = validate_code(code_str, puzzle_dict, timeout=10)
"""
import ast
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

# Mirror eval_collect_failures.py's contract.
ALLOWED_IMPORTS = {"math", "collections", "itertools", "copy", "functools",
                   "operator", "statistics", "heapq", "bisect", "re"}
BLOCKED_SUBSTRINGS = ("import os", "import sys", "subprocess", "socket",
                      "requests", "pathlib", "shutil", "open(", "eval(",
                      "exec(", "__import__", "compile(", "input(", "importlib",
                      "ctypes", "multiprocessing", "threading", "pickle")

TIMEOUT_S = 10


def parse_grid(s: str):
    return [[int(c) for c in line] for line in s.strip().split("\n") if line.strip()]


def load_puzzle(path):
    raw = json.loads(Path(path).read_text())
    return {
        "train": [{"input": parse_grid(p["input"]), "output": parse_grid(p["output"])}
                  for p in raw["train"]],
        "test":  [{"input": parse_grid(p["input"]), "output": parse_grid(p["output"])}
                  for p in raw["test"]],
    }


def _static_checks(code: str):
    """Cheap rejects before we even run it: must parse, must define solve,
    must not use blocked operations, imports must be in the allowlist."""
    errs = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax_error: {e}"]
    has_solve = any(isinstance(n, ast.FunctionDef) and n.name == "solve"
                    for n in ast.walk(tree))
    if not has_solve:
        errs.append("no def solve")
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    errs.append(f"blocked import: {a.name}")
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                errs.append(f"blocked import-from: {n.module}")
    low = code
    for bad in BLOCKED_SUBSTRINGS:
        if bad in low and not bad.startswith("import "):
            errs.append(f"blocked op: {bad}")
    return errs


# Subprocess runner: exec the code, run solve on each pair, emit per-pair result.
_RUNNER = r'''
import json, sys, copy
code = open(sys.argv[1]).read()
puzzle = json.load(open(sys.argv[2]))
ns = {}
try:
    exec(code, ns)
    solve = ns["solve"]
except Exception as e:
    print(json.dumps({"exec_error": f"{type(e).__name__}: {e}"})); sys.exit(0)

def grid_ok(g):
    if not isinstance(g, list) or not g: return False
    if not all(isinstance(r, list) and r for r in g): return False
    w = len(g[0])
    if any(len(r) != w for r in g): return False
    for r in g:
        for v in r:
            if not isinstance(v, int) or v < 0 or v > 9: return False
    return True

pairs = []
for kind in ("train", "test"):
    for i, p in enumerate(puzzle[kind]):
        rec = {"type": kind, "idx": i}
        try:
            out = solve(copy.deepcopy(p["input"]))
        except Exception as e:
            rec.update(passed=False, error=f"{type(e).__name__}: {e}"); pairs.append(rec); continue
        if not grid_ok(out):
            rec.update(passed=False, error="bad_return: not a rectangular list[list[int 0-9]]"); pairs.append(rec); continue
        exp = p["output"]
        if len(out) != len(exp) or any(len(a) != len(b) for a, b in zip(out, exp)):
            rec.update(passed=False, error=f"wrong_shape: got {len(out)}x{len(out[0])} want {len(exp)}x{len(exp[0])}"); pairs.append(rec); continue
        diff = sum(1 for ra, rb in zip(out, exp) for a, b in zip(ra, rb) if a != b)
        rec.update(passed=(diff == 0), cell_diff=diff, error=None); pairs.append(rec)
print(json.dumps({"exec_error": None, "pairs": pairs}))
'''


def validate_code(code: str, puzzle: dict, timeout: int = TIMEOUT_S) -> dict:
    """Return {overall_pass, exec_error, static_errors, pairs:[...]}.
    overall_pass iff no static errors, no exec error, and every pair passed."""
    static = _static_checks(code)
    if static:
        return {"overall_pass": False, "static_errors": static,
                "exec_error": None, "pairs": []}
    with tempfile.TemporaryDirectory() as d:
        cf = os.path.join(d, "code.py"); pf = os.path.join(d, "puz.json")
        Path(cf).write_text(code)
        Path(pf).write_text(json.dumps(puzzle))
        rf = os.path.join(d, "run.py"); Path(rf).write_text(_RUNNER)
        try:
            r = subprocess.run([sys.executable, rf, cf, pf],
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"overall_pass": False, "static_errors": [],
                    "exec_error": f"timeout>{timeout}s", "pairs": []}
        try:
            out = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return {"overall_pass": False, "static_errors": [],
                    "exec_error": f"runner_crash: {r.stderr[-300:]}", "pairs": []}
    if out.get("exec_error"):
        out["overall_pass"] = False; out.setdefault("static_errors", [])
        out.setdefault("pairs", []); return out
    pairs = out.get("pairs", [])
    out["overall_pass"] = bool(pairs) and all(p.get("passed") for p in pairs)
    out["static_errors"] = []
    return out


def main():
    if len(sys.argv) != 3:
        print("usage: validate_solver.py <puzzle.json> <solver.py>", file=sys.stderr)
        sys.exit(2)
    puzzle = load_puzzle(sys.argv[1])
    code = Path(sys.argv[2]).read_text()
    res = validate_code(code, puzzle)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["overall_pass"] else 1)


if __name__ == "__main__":
    main()
