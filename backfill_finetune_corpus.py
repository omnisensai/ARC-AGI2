"""Backfill the fine-tuning corpus from existing Model Results/ + research/true_solves/.

Walks every iter_N_response.py under Model Results/<Model>/<puzzle>/ and the
canonical solver under research/true_solves/<puzzle>_<model>.py if present,
re-runs each against the puzzle file to get training pass count + test diff,
and appends one record per attempt to research/finetune_corpus/.

Idempotent: re-running replaces existing records keyed on
(puzzle_id, model, iter). Records migrate buckets if their label changed.

Usage:
    python backfill_finetune_corpus.py            # walk everything
    python backfill_finetune_corpus.py 13e47133   # one puzzle only
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

from finetune_corpus import (
    append_record,
    build_record,
    compute_training_stats,
)


MODEL_RESULTS = Path("Model Results")
TRUE_SOLVES = Path("research/true_solves")
EVAL_DIR = Path("evaluation")


def load_solve(code_path):
    spec = importlib.util.spec_from_file_location("_bf_sol", str(code_path))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    if not hasattr(mod, "solve"):
        return None
    return mod


def compute_test_diff(mod, puzzle):
    """Sum diff across every test pair that has ground truth. None if any errored."""
    test_pairs = [t for t in puzzle.get("test", []) if "output" in t]
    if not test_pairs:
        return None
    total = 0
    for tp in test_pairs:
        try:
            out = mod.solve(tp["input"])
        except Exception:
            return None
        truth = tp["output"]
        if not isinstance(out, list) or not out or not isinstance(out[0], list):
            return None
        if len(out) != len(truth) or any(
            len(out[r]) != len(truth[r]) for r in range(len(truth))
        ):
            return None
        total += sum(
            1 for r in range(len(truth)) for c in range(len(truth[0]))
            if out[r][c] != truth[r][c]
        )
    return total


def derive_test_label(test_diff):
    if test_diff is None:
        return None
    if test_diff == 0:
        return "TRUE_SOLVE"
    if test_diff <= 20:
        return "NEAR_MISS"
    return "FALSE_CONFIDENT_SUBMIT"


def backfill_one_iter(puzzle_id, model_name, iter_n, code_path, puzzle, source_label):
    """Read code + rule, run, build and append record. Returns label or None."""
    code = code_path.read_text()
    rule_path = code_path.parent / f"iter_{iter_n}_rule.txt"
    stated_rule = rule_path.read_text().strip() if rule_path.exists() else None

    mod = load_solve(code_path)
    if mod is None:
        return None
    train_pass, train_diff = compute_training_stats(mod, puzzle.get("train", []))
    test_diff = compute_test_diff(mod, puzzle)
    test_label = derive_test_label(test_diff)

    record = build_record(
        puzzle_id=puzzle_id,
        model=model_name,
        iter_n=iter_n,
        code=code,
        stated_rule=stated_rule,
        training_pass=train_pass,
        training_total=len(puzzle.get("train", [])),
        training_diff_total=train_diff,
        test_diff_total=test_diff,
        test_label=test_label,
        source_path=str(code_path),
    )
    if record is None:
        return None
    append_record(record)
    return record["label"]


def backfill_all(puzzle_filter=None):
    counts = {"wrong_training": 0, "wrong_test": 0, "correct": 0, "skipped": 0}
    seen_puzzles = set()

    # 1. Walk Model Results/<Model>/<puzzle>/iter_N_response.py
    if MODEL_RESULTS.exists():
        for model_dir in sorted(MODEL_RESULTS.iterdir()):
            if not model_dir.is_dir():
                continue
            model_name = model_dir.name
            for puzzle_dir in sorted(model_dir.iterdir()):
                if not puzzle_dir.is_dir():
                    continue
                puzzle_id = puzzle_dir.name
                if puzzle_filter and puzzle_id != puzzle_filter:
                    continue
                puzzle_file = EVAL_DIR / f"{puzzle_id}.json"
                if not puzzle_file.exists():
                    counts["skipped"] += 1
                    continue
                puzzle = json.loads(puzzle_file.read_text())
                seen_puzzles.add(puzzle_id)

                for code_path in sorted(puzzle_dir.glob("iter_*_response.py")):
                    m = re.match(r"iter_(\d+)_response\.py", code_path.name)
                    if not m:
                        continue
                    iter_n = int(m.group(1))
                    label = backfill_one_iter(
                        puzzle_id, model_name, iter_n, code_path, puzzle,
                        source_label="Model Results",
                    )
                    if label:
                        counts[label] += 1
                    else:
                        counts["skipped"] += 1

    # 2. Walk research/true_solves/<puzzle>_<Model>.py (canonical curated solvers)
    if TRUE_SOLVES.exists():
        for path in sorted(TRUE_SOLVES.glob("*_*.py")):
            stem = path.stem
            parts = stem.split("_", 1)
            if len(parts) != 2:
                continue
            puzzle_id, model_name = parts
            if puzzle_filter and puzzle_id != puzzle_filter:
                continue
            puzzle_file = EVAL_DIR / f"{puzzle_id}.json"
            if not puzzle_file.exists():
                counts["skipped"] += 1
                continue
            puzzle = json.loads(puzzle_file.read_text())
            seen_puzzles.add(puzzle_id)
            # Use a sentinel iter index of 0 to mark "canonical curated solver"
            # so it doesn't collide with iter_N from Model Results.
            label = backfill_one_iter(
                puzzle_id, model_name, 0, path, puzzle,
                source_label="research/true_solves",
            )
            if label:
                counts[label] += 1
            else:
                counts["skipped"] += 1

    return counts, seen_puzzles


def main():
    puzzle_filter = sys.argv[1] if len(sys.argv) > 1 else None
    counts, puzzles = backfill_all(puzzle_filter)
    print(json.dumps({
        "puzzles_seen": sorted(puzzles),
        "puzzle_count": len(puzzles),
        "records": counts,
    }, indent=2))


if __name__ == "__main__":
    main()
