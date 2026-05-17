"""
Backfill the research/ corpus from existing Model Results/ artifacts.

For each (model, puzzle_id) pair, walks all iter_N_response.py files in iter
order and applies the same labeling/saving logic that paste_helper would have
applied if --label had been set at the time.

Usage:
  python backfill_research_corpus.py [--corpus-root research]
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

from research_mode import (
    append_calibration_row,
    label_outcome,
    save_corpus_artifacts,
    write_final_label,
)


ITER_RE = re.compile(r"iter_(\d+)_response\.py$")


def evaluate_solver_on_training(puzzle_file, solution_path):
    """Return (training_pass_count, total_pairs)."""
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    train = puzzle.get("train", [])
    if not train:
        return 0, 0
    spec = importlib.util.spec_from_file_location("_backfill_sol", str(solution_path))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return 0, len(train)
    if not hasattr(mod, "solve"):
        return 0, len(train)
    passed = 0
    for pair in train:
        try:
            if mod.solve(pair["input"]) == pair["output"]:
                passed += 1
        except Exception:
            return passed, len(train)
    return passed, len(train)


def collect_iters(puzzle_dir):
    iters = []
    for path in sorted(puzzle_dir.glob("iter_*_response.py")):
        m = ITER_RE.search(path.name)
        if m:
            iters.append(int(m.group(1)))
    return sorted(iters)


def find_evaluation_dir(repo_root):
    candidates = [repo_root / "evaluation", repo_root / "Evaluation"]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def process_puzzle_run(model_dir, model_name, puzzle_dir, puzzle_id,
                      eval_dir, corpus_root):
    puzzle_file = eval_dir / f"{puzzle_id}.json"
    if not puzzle_file.exists():
        return {"puzzle_id": puzzle_id, "model": model_name,
                "skipped": "puzzle file not in evaluation/"}

    iter_ns = collect_iters(puzzle_dir)
    if not iter_ns:
        return {"puzzle_id": puzzle_id, "model": model_name, "skipped": "no iters"}

    results = []
    prev_iter_data = None
    for n in iter_ns:
        code_path = puzzle_dir / f"iter_{n}_response.py"
        feedback_path = puzzle_dir / f"iter_{n}_feedback.txt"
        summary_path = puzzle_dir / f"iter_{n}_summary.json"

        passed, total = evaluate_solver_on_training(puzzle_file, code_path)
        train_pass_rate = passed / total if total else 0.0

        prev_summary = None
        if summary_path.exists():
            try:
                prev_summary = json.loads(summary_path.read_text())
            except Exception:
                prev_summary = None

        if train_pass_rate < 1.0:
            prev_iter_data = {
                "iter": n,
                "code_path": str(code_path),
                "summary": prev_summary or {
                    "code_test_result": {"diffs": None}
                },
            }
            results.append({"iter": n, "training_pass_rate": train_pass_rate,
                            "skipped": "training did not pass"})
            continue

        label_data = label_outcome(str(puzzle_file), str(code_path))

        write_final_label(puzzle_dir, label_data, n, train_pass_rate)

        written = save_corpus_artifacts(
            puzzle_id, model_name, n, str(code_path),
            str(feedback_path) if feedback_path.exists() else None,
            label_data, prev_iter_data=prev_iter_data,
            corpus_root=corpus_root,
        )

        append_calibration_row(
            puzzle_id, model_name, n, train_pass_rate, label_data,
            corpus_root=corpus_root,
        )

        results.append({
            "iter": n,
            "training_pass_rate": train_pass_rate,
            "label": label_data.get("label"),
            "test_diff_count": label_data.get("test_diff_count"),
            "corpus": written,
        })

        prev_iter_data = {
            "iter": n,
            "code_path": str(code_path),
            "summary": prev_summary or {
                "code_test_result": {
                    "matches": label_data.get("label") == "TRUE_SOLVE",
                    "diffs": label_data.get("test_diff_count", 0),
                }
            },
        }

    return {"puzzle_id": puzzle_id, "model": model_name, "iters": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".",
                        help="Repository root (containing Model Results/ and evaluation/).")
    parser.add_argument("--corpus-root", default="research",
                        help="Output corpus directory.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    corpus_root = (repo_root / args.corpus_root).resolve()

    model_results_dir = repo_root / "Model Results"
    if not model_results_dir.is_dir():
        print(f"ERROR: {model_results_dir} not found", file=sys.stderr)
        sys.exit(1)

    eval_dir = find_evaluation_dir(repo_root)
    if eval_dir is None:
        print(f"ERROR: no evaluation/ directory under {repo_root}", file=sys.stderr)
        sys.exit(1)

    summary = []
    for model_dir in sorted(model_results_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        model_name = model_dir.name
        for puzzle_dir in sorted(model_dir.iterdir()):
            if not puzzle_dir.is_dir():
                continue
            puzzle_id = puzzle_dir.name
            result = process_puzzle_run(
                model_dir, model_name, puzzle_dir, puzzle_id,
                eval_dir, corpus_root,
            )
            summary.append(result)

    print(json.dumps({
        "corpus_root": str(corpus_root),
        "processed": len(summary),
        "results": summary,
    }, indent=2))


if __name__ == "__main__":
    main()
