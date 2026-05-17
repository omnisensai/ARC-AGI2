"""
Research-mode corpus saving.

When training pairs all pass (submit-eligible) AND we're running with access to
test ground truth (puzzles in evaluation/ have it), label the outcome and save
artifacts into a corpus structure for offline learning:

  research/
    true_solves/<puzzle>__<model>__iter<N>.py
    bug_fixes/<bug_class>/<puzzle>__<model>__iter<N-1>_to_<N>/
      before.py  after.py  feedback.txt  diff.patch  meta.json
    false_confident_submits/<puzzle>__<model>__iter<N>/
      code.py  test_diff.json  error_pattern.json
    near_misses/<puzzle>__<model>__iter<N>/
      code.py  test_diff.json  error_pattern.json
    calibration/outcomes.csv

Operates in research mode only — never reads test ground truth during the
iteration loop. Only after submit-eligible (training pass rate = 1.0).
"""

import csv
import difflib
import importlib.util
import json
import shutil
from pathlib import Path

from feedback_diagnostics import (
    color_distribution_overlap,
    error_cluster_density,
    transformation_count_match,
)


CORPUS_ROOT_DEFAULT = Path("research")
NEAR_MISS_THRESHOLD = 20  # test_diff below this counts as near-miss


def _safe_solve(solution_path, test_input):
    spec = importlib.util.spec_from_file_location("_research_sol", str(solution_path))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod.solve(test_input), None
    except Exception as e:
        return None, str(e)


def _grid_diff(a, b):
    if a is None or b is None:
        return None
    if len(a) != len(b) or any(len(a[r]) != len(b[r]) for r in range(len(a))):
        return None
    return [
        [r, c]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def _signals(input_grid, expected, actual):
    return {
        "transformation_match": transformation_count_match(input_grid, expected, actual),
        "color_distribution_overlap": color_distribution_overlap(expected, actual),
        "error_cluster_density": error_cluster_density(expected, actual),
    }


def label_outcome(puzzle_file, solution_path):
    """Compute outcome label by running solve on test_input and comparing to ground truth.

    Returns dict with label, test_diff_count, diff_cells, signals. Caller is
    responsible for only invoking this when training pass rate == 1.0 AND the
    puzzle has known test ground truth (research mode only).
    """
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    test = puzzle.get("test", [])
    if not test or "output" not in test[0]:
        return {"label": "NO_GROUND_TRUTH"}

    test_input = test[0]["input"]
    truth = test[0]["output"]

    actual, err = _safe_solve(solution_path, test_input)
    if err is not None:
        return {"label": "SOLVER_ERROR", "error": err}

    diff_cells = _grid_diff(actual, truth)
    if diff_cells is None:
        return {"label": "DIM_MISMATCH"}

    diff_count = len(diff_cells)
    if diff_count == 0:
        label = "TRUE_SOLVE"
    elif diff_count <= NEAR_MISS_THRESHOLD:
        label = "NEAR_MISS"
    else:
        label = "FALSE_CONFIDENT_SUBMIT"

    return {
        "label": label,
        "test_diff_count": diff_count,
        "test_total_cells": len(truth) * len(truth[0]),
        "diff_cells": diff_cells,
        "signals": _signals(test_input, truth, actual),
    }


def detect_bug_fix(prev_summary, current_summary):
    """Did the current iter improve meaningfully over the previous?

    Returns the bug_class label if so (matched detector from prev iter's
    feedback if available, or "untyped_improvement"), else None.
    """
    if not prev_summary or not current_summary:
        return None

    prev_test = (prev_summary.get("code_test_result") or {}).get("diffs")
    curr_test = (current_summary.get("code_test_result") or {}).get("diffs")
    if prev_test is None or curr_test is None:
        return None

    if curr_test < prev_test - 5 or (prev_test > 0 and curr_test == 0):
        return prev_summary.get("matched_bug_class") or "untyped_improvement"
    return None


def save_corpus_artifacts(
    puzzle_id, model, iter_n, code_path, feedback_path,
    label_data, prev_iter_data=None, corpus_root=CORPUS_ROOT_DEFAULT,
):
    """Save artifacts to corpus directory per the label and iter context.

    label_data: dict from label_outcome()
    prev_iter_data: optional dict with keys 'iter', 'code_path', 'summary',
                    used to detect successful bug fixes.

    Returns dict of paths written.
    """
    corpus_root = Path(corpus_root)
    label = label_data.get("label", "UNLABELED")
    written = {}
    base_name = f"{puzzle_id}__{model}__iter{iter_n}"

    if label == "TRUE_SOLVE":
        dest = corpus_root / "true_solves" / f"{base_name}.py"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(code_path, dest)
        written["true_solve"] = str(dest)

    elif label == "FALSE_CONFIDENT_SUBMIT":
        dest_dir = corpus_root / "false_confident_submits" / base_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(code_path, dest_dir / "code.py")
        (dest_dir / "test_diff.json").write_text(json.dumps({
            "test_diff_count": label_data["test_diff_count"],
            "diff_cells": label_data["diff_cells"],
        }, indent=2))
        (dest_dir / "error_pattern.json").write_text(json.dumps({
            "puzzle_id": puzzle_id,
            "model": model,
            "iter": iter_n,
            "signals": label_data.get("signals", {}),
            "candidate_for_new_detector": True,
        }, indent=2))
        written["false_confident"] = str(dest_dir)

    elif label == "NEAR_MISS":
        dest_dir = corpus_root / "near_misses" / base_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(code_path, dest_dir / "code.py")
        (dest_dir / "test_diff.json").write_text(json.dumps({
            "test_diff_count": label_data["test_diff_count"],
            "diff_cells": label_data["diff_cells"],
        }, indent=2))
        (dest_dir / "error_pattern.json").write_text(json.dumps({
            "puzzle_id": puzzle_id,
            "model": model,
            "iter": iter_n,
            "signals": label_data.get("signals", {}),
        }, indent=2))
        written["near_miss"] = str(dest_dir)

    bug_class = None
    if prev_iter_data:
        bug_class = detect_bug_fix(
            prev_iter_data.get("summary"),
            {"code_test_result": {"diffs": label_data.get("test_diff_count", 0)}}
            if label == "TRUE_SOLVE"
            else prev_iter_data.get("summary"),
        )
        if bug_class and label == "TRUE_SOLVE":
            fix_dir = (corpus_root / "bug_fixes" / bug_class /
                       f"{puzzle_id}__{model}__iter{prev_iter_data['iter']}_to_{iter_n}")
            fix_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy(prev_iter_data["code_path"], fix_dir / "before.py")
            shutil.copy(code_path, fix_dir / "after.py")
            if feedback_path and Path(feedback_path).exists():
                shutil.copy(feedback_path, fix_dir / "feedback.txt")

            before_text = Path(prev_iter_data["code_path"]).read_text().splitlines(keepends=True)
            after_text = Path(code_path).read_text().splitlines(keepends=True)
            diff = list(difflib.unified_diff(
                before_text, after_text,
                fromfile=f"iter{prev_iter_data['iter']}.py",
                tofile=f"iter{iter_n}.py",
                lineterm="",
            ))
            (fix_dir / "diff.patch").write_text("".join(diff))

            (fix_dir / "meta.json").write_text(json.dumps({
                "puzzle_id": puzzle_id,
                "model": model,
                "from_iter": prev_iter_data["iter"],
                "to_iter": iter_n,
                "bug_class": bug_class,
                "score_before": (prev_iter_data.get("summary") or {}).get("code_test_result"),
                "score_after": {
                    "matches": True, "diffs": 0,
                    "total": label_data.get("test_total_cells"),
                },
            }, indent=2))
            written["bug_fix"] = str(fix_dir)

    return written


def append_calibration_row(
    puzzle_id, model, iter_n, training_pass_rate, label_data,
    corpus_root=CORPUS_ROOT_DEFAULT,
):
    """Append one outcome row to research/calibration/outcomes.csv."""
    corpus_root = Path(corpus_root)
    cal_dir = corpus_root / "calibration"
    cal_dir.mkdir(parents=True, exist_ok=True)
    csv_path = cal_dir / "outcomes.csv"

    fieldnames = [
        "puzzle_id", "model", "iter", "training_pass_rate",
        "transformation_match", "color_distribution_overlap",
        "error_cluster_density", "label", "test_diff_count",
    ]

    is_new = not csv_path.exists()
    signals = label_data.get("signals", {})

    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "puzzle_id": puzzle_id,
            "model": model,
            "iter": iter_n,
            "training_pass_rate": f"{training_pass_rate:.4f}",
            "transformation_match": f"{signals.get('transformation_match', 0):.4f}",
            "color_distribution_overlap": f"{signals.get('color_distribution_overlap', 0):.4f}",
            "error_cluster_density": f"{signals.get('error_cluster_density', 0):.4f}",
            "label": label_data.get("label", "UNLABELED"),
            "test_diff_count": label_data.get("test_diff_count", ""),
        })

    return str(csv_path)


def write_final_label(out_dir, label_data, iter_n, training_pass_rate):
    """Write the per-puzzle final_label.json next to the iter artifacts."""
    out = Path(out_dir) / "final_label.json"
    payload = dict(label_data)
    payload["submitted_at_iter"] = iter_n
    payload["training_pass_rate"] = training_pass_rate
    out.write_text(json.dumps(payload, indent=2))
    return str(out)
