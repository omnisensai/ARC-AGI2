"""Cross-cut closeness analyzer for eval_collect_failures runs.

The failure_bucket labels distinguish "code runs vs doesn't". This script
rebuckets the same attempts along a richer 'how close was the model to the
right rule' axis, using exception types and cell-accuracy together.

Usage:
    python scripts/closeness_analyzer.py [--run <dir>] [--by-shape]

Reads the per-attempt JSONs produced by eval_collect_failures.py.
"""
import argparse, glob, json
from collections import Counter, defaultdict
from pathlib import Path

# trivially-fixable exception types (typically one-line fixes)
TRIVIAL_EXC = {"NameError", "ImportError", "ModuleNotFoundError"}
# semantic bugs that suggest the model had the wrong idea about types/indexing
SEMANTIC_EXC = {"IndexError", "KeyError", "ValueError", "ZeroDivisionError",
                "AttributeError", "TypeError", "RecursionError", "ArithmeticError"}

# Ordered for readability: best -> worst rule understanding
ORDER = [
    "solver_positive", "near_miss", "partial_rule",
    "wrong_rule_runnable",
    "trivial_fix_repair", "semantic_bug_repair", "exec_other",
    "shape_contract", "contract_other",
    "syntax_minor", "syntax_major",
    "timeout", "no_code",
]


def closeness(rec):
    """Map a saved attempt record to a closeness category."""
    bucket = rec["failure_bucket"]
    if bucket == "correct":
        return "solver_positive"
    if bucket in ("near_miss_95", "near_miss_90"):
        return "near_miss"
    if bucket == "wrong_training":
        avg = (rec.get("aggregate") or {}).get("avg_train_cell_accuracy") or 0
        return "partial_rule" if avg >= 0.5 else "wrong_rule_runnable"
    if bucket == "wrong_shape":
        return "shape_contract"
    if bucket in ("train_no_grid", "non_rectangular", "bad_cell_values"):
        return "contract_other"
    if bucket == "syntax_error":
        msg = (rec["execution"].get("exception_message") or "")
        import re
        m = re.search(r"line (\d+)", msg)
        if m:
            line = int(m.group(1))
            code = rec.get("extracted_code") or ""
            total_lines = len(code.splitlines())
            if total_lines and line >= total_lines - 3:
                return "syntax_minor"
        return "syntax_major"
    if bucket == "exec_error":
        exc_types = set()
        for t in rec.get("train_results", []):
            et = t.get("exception_type")
            if et: exc_types.add(et)
        et = rec["execution"].get("exception_type")
        if et: exc_types.add(et)
        if exc_types & TRIVIAL_EXC:
            return "trivial_fix_repair"
        if exc_types & SEMANTIC_EXC:
            return "semantic_bug_repair"
        return "exec_other"
    if bucket == "timeout":
        return "timeout"
    if bucket == "no_code":
        return "no_code"
    return f"other_{bucket}"


def shape_type(rec):
    """Return same_size / diff_size / mixed / unknown based on saved shapes."""
    shapes = rec.get("shapes", {})
    same_per_pair = [
        t["input_shape"] == t["expected_output_shape"]
        for t in shapes.get("train", [])
    ]
    if shapes.get("known_test_output_shape"):
        same_per_pair.append(
            shapes["test_input_shape"] == shapes["known_test_output_shape"]
        )
    if not same_per_pair:
        return "unknown"
    if all(same_per_pair):
        return "same_size"
    if not any(same_per_pair):
        return "diff_size"
    return "mixed"


def analyze(run_dir, by_shape=False):
    by_closeness = Counter()
    by_closeness_and_shape = defaultdict(Counter)
    exc_counts = Counter()
    closeness_examples = defaultdict(list)

    files = sorted(glob.glob(f"{run_dir}/attempts/*.json"))
    for f in files:
        try:
            rec = json.load(open(f))
        except Exception:
            continue
        c = closeness(rec)
        by_closeness[c] += 1
        if by_shape:
            by_closeness_and_shape[c][shape_type(rec)] += 1
        for t in rec.get("train_results", []):
            et = t.get("exception_type")
            if et: exc_counts[et] += 1
        if len(closeness_examples[c]) < 2:
            closeness_examples[c].append((rec["puzzle_id"], rec["attempt_id"]))

    total = sum(by_closeness.values()) or 1

    print(f"{'closeness':25s}  {'count':>5s}  {'pct':>6s}  examples")
    print("-" * 90)
    for c in ORDER:
        n = by_closeness.get(c, 0)
        if n == 0:
            continue
        ex = ", ".join(f"{p}_a{a}" for p, a in closeness_examples[c][:2])
        print(f"  {c:23s}  {n:5d}  {100*n/total:5.1f}%  {ex}")

    if by_shape:
        print(f"\n{'closeness':25s}  same  diff  mixed")
        print("-" * 60)
        for c in ORDER:
            if c not in by_closeness_and_shape:
                continue
            s = by_closeness_and_shape[c]
            print(f"  {c:23s}  {s.get('same_size',0):4d}  {s.get('diff_size',0):4d}  {s.get('mixed',0):4d}")

    print(f"\n=== top per-pair exception types ===")
    for t, n in exc_counts.most_common(15):
        tag = "trivial" if t in TRIVIAL_EXC else ("semantic" if t in SEMANTIC_EXC else "")
        print(f"  {t:25s}  {n:5d}  {tag}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="run dir; default = newest in /root/eval_runs or ./eval_runs")
    ap.add_argument("--by-shape", action="store_true",
                    help="also break down by same-size vs diff-size puzzles")
    args = ap.parse_args()

    if args.run is None:
        for root in ("/root/eval_runs", "./eval_runs"):
            p = Path(root)
            if not p.exists():
                continue
            subs = sorted(p.iterdir(), key=lambda x: x.stat().st_mtime)
            if subs:
                args.run = str(subs[-1])
                break
    if not args.run:
        raise SystemExit("no run dir found; pass --run")
    print(f"analyzing: {args.run}\n")
    analyze(args.run, by_shape=args.by_shape)
