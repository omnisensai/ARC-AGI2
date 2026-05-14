"""
Paste helper: process a manual chat-mode response and save artifacts.

When the user pastes a model response (from claude.ai / chatgpt.com / gemini /
grok web browser), this script:
  1. Extracts def solve() and TEST_OUTPUT (hand grid)
  2. Runs run_feedback.py against the puzzle
  3. Saves all artifacts under Model Results/<Model>/<puzzle>/iter_N_*
  4. Prints a JSON manifest of paths so the caller can push to GitHub

Usage:
  python paste_helper.py <puzzle_id> <model> <paste_file> [--iter N]

Example:
  python paste_helper.py 13e47133 gemini /tmp/paste.txt
"""

import argparse
import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path


MODEL_DIR = {
    "claude":     "Claude",
    "gpt":        "GPT",
    "gemini":     "Gemini",
    "grok":       "Grok",
    "openrouter": "OpenRouter",
}


def extract_solve(text):
    fence_matches = re.findall(
        r"```(?:python)?\s*\n([\s\S]*?def solve\b[\s\S]*?)\n```",
        text,
    )
    if fence_matches:
        return fence_matches[-1].rstrip()
    raw_matches = re.findall(
        r"^(def solve\b[\s\S]*?)(?=\n```|\n# end|\Z)",
        text, re.MULTILINE,
    )
    if raw_matches:
        return raw_matches[-1].rstrip()
    return None


def extract_hand_grid(text):
    m = re.search(r"TEST_OUTPUT\s*=\s*\[", text)
    if not m:
        return None
    start = m.end() - 1
    depth = 0
    end = None
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None
    try:
        grid = ast.literal_eval(text[start:end])
        if (isinstance(grid, list)
                and all(isinstance(row, list) for row in grid)
                and all(isinstance(v, int) for row in grid for v in row)):
            return grid
    except (ValueError, SyntaxError):
        pass
    return None


def validate_hand_grid(hand_grid, puzzle_file):
    if hand_grid is None:
        return None
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    if not puzzle.get("test") or "output" not in puzzle["test"][0]:
        return None
    truth = puzzle["test"][0]["output"]
    if len(hand_grid) != len(truth) or any(
        len(hand_grid[r]) != len(truth[r]) for r in range(len(truth))
    ):
        return {"dimension_mismatch": True}
    diffs = sum(
        1 for r in range(len(truth)) for c in range(len(truth[0]))
        if hand_grid[r][c] != truth[r][c]
    )
    total = len(truth) * len(truth[0])
    return {"matches": diffs == 0, "diffs": diffs, "total": total}


def validate_code_on_test(puzzle_file, solution_path):
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    if not puzzle.get("test") or "output" not in puzzle["test"][0]:
        return None
    test_input = puzzle["test"][0]["input"]
    truth = puzzle["test"][0]["output"]
    spec = importlib.util.spec_from_file_location("_iter_sol", solution_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        out = mod.solve(test_input)
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    if not isinstance(out, list) or not out or not isinstance(out[0], list):
        return {"status": "error", "msg": "solve() did not return 2D list"}
    if len(out) != len(truth) or any(
        len(out[r]) != len(truth[r]) for r in range(len(truth))
    ):
        return {"status": "dim_mismatch", "got": f"{len(out)}x{len(out[0])}"}
    diffs = sum(
        1 for r in range(len(truth)) for c in range(len(truth[0]))
        if out[r][c] != truth[r][c]
    )
    total = len(truth) * len(truth[0])
    return {"matches": diffs == 0, "diffs": diffs, "total": total}


def next_iter_n(model_dir):
    """Default to iter 1 (overwrite) when no explicit --iter given.

    Rationale: when the user pastes <puzzle>__<model>.txt (no __iterN suffix),
    that means a fresh chat session, which is iter 1. The auto-increment
    behavior we used before treated fresh runs as continuations of any old
    iter files lying around, which caused the regression detector to fire
    spuriously against unrelated code.

    For continuations within the same chat, the user passes an explicit
    --iter N or uses the __iterN filename suffix (workflow translates that
    to --iter N).
    """
    return 1


def compute_diagnosis(puzzle_file, solution_path, prev_code_path=None,
                      current_code_path=None, iter_n=None):
    """Run solver on every training pair, classify phase, match bug-class
    fingerprints, run structural-diff (if rule_comprehension), and detect
    iter-over-iter regression (if prev/current code provided).

    Returns formatted feedback block to prepend, or None if diagnosis can't run.
    Handles three failure modes specially:
      - Module won't load (SyntaxError, ImportError): emit syntax_error diagnosis
      - solve() raises an exception on a training pair: emit runtime_error diagnosis
      - solve() returns malformed output: emit malformed_output diagnosis
    """
    try:
        from feedback_diagnostics import diagnose_full, format_targeted_feedback
    except ImportError:
        return None

    with open(puzzle_file) as f:
        puzzle = json.load(f)

    spec = importlib.util.spec_from_file_location("_iter_sol_diag", solution_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        return _format_syntax_error(e)
    except Exception as e:
        return _format_module_load_error(e)

    if not hasattr(mod, "solve"):
        return _format_missing_solve()

    actual_outputs = []
    for idx, pair in enumerate(puzzle.get("train", []), 1):
        try:
            out = mod.solve(pair["input"])
        except Exception as e:
            return _format_runtime_error(idx, e, solution_path)
        if not isinstance(out, list) or not out or not isinstance(out[0], list):
            return _format_malformed_output(idx, out)
        actual_outputs.append(out)

    prev_code = None
    current_code = None
    prev_actual_outputs = None
    if prev_code_path and Path(prev_code_path).exists():
        prev_code = Path(prev_code_path).read_text()
        # Re-run prior iter on training pairs for cell-level regression check.
        prev_spec = importlib.util.spec_from_file_location("_prev_sol", prev_code_path)
        prev_mod = importlib.util.module_from_spec(prev_spec)
        try:
            prev_spec.loader.exec_module(prev_mod)
            if hasattr(prev_mod, "solve"):
                prev_actual_outputs = []
                for pair in puzzle.get("train", []):
                    try:
                        prev_actual_outputs.append(prev_mod.solve(pair["input"]))
                    except Exception:
                        prev_actual_outputs.append(None)
        except Exception:
            prev_actual_outputs = None
    if current_code_path and Path(current_code_path).exists():
        current_code = Path(current_code_path).read_text()

    diag = diagnose_full(puzzle, actual_outputs,
                         prev_code=prev_code, current_code=current_code,
                         prev_actual_outputs=prev_actual_outputs)
    if diag.get("phase") is None and not diag.get("regression_alert"):
        return None

    return format_targeted_feedback(diag, iter_n=iter_n)


def _format_runtime_error(pair_idx, exc, solution_path):
    import traceback
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    relevant = [line for line in tb if "solution.py" in line or "_iter_sol_diag" in line]
    location = relevant[-1].strip() if relevant else ""

    return (
        "=" * 80 + "\n"
        "DIAGNOSIS\n"
        + "=" * 80 + "\n\n"
        f"Phase: runtime_error\n\n"
        f"Your code raised an exception when called on training pair {pair_idx}:\n\n"
        f"  {type(exc).__name__}: {exc}\n"
        f"  {location}\n\n"
        f"Fix the runtime error first. Until your code runs without crashing on every "
        f"training pair, no algorithmic diagnosis is possible. Common causes:\n"
        f"  - Calling numpy/Counter operations on empty arrays/lists\n"
        f"  - Indexing into a list before checking it has elements\n"
        f"  - Division by zero / modulo zero when a denominator can be zero\n"
        f"  - Assuming a color exists in the input when it might not"
    )


def _format_syntax_error(exc):
    return (
        "=" * 80 + "\n"
        "DIAGNOSIS\n"
        + "=" * 80 + "\n\n"
        f"Phase: syntax_error\n\n"
        f"Your code has a Python syntax error and cannot be loaded:\n\n"
        f"  {type(exc).__name__}: {exc}\n\n"
        f"Fix the syntax error before anything else."
    )


def _format_module_load_error(exc):
    return (
        "=" * 80 + "\n"
        "DIAGNOSIS\n"
        + "=" * 80 + "\n\n"
        f"Phase: module_load_error\n\n"
        f"Your code raised an exception at module load (top-level statement, not "
        f"inside def solve):\n\n"
        f"  {type(exc).__name__}: {exc}\n\n"
        f"Move imports and constants inside def solve, or fix the top-level code."
    )


def _format_missing_solve():
    return (
        "=" * 80 + "\n"
        "DIAGNOSIS\n"
        + "=" * 80 + "\n\n"
        f"Phase: missing_solve\n\n"
        f"Your response does not contain a `def solve(input_grid):` function. "
        f"All responses must define solve() — we run your code, we don't read "
        f"prose explanations."
    )


def _format_malformed_output(pair_idx, out):
    return (
        "=" * 80 + "\n"
        "DIAGNOSIS\n"
        + "=" * 80 + "\n\n"
        f"Phase: malformed_output\n\n"
        f"Your solve() function on training pair {pair_idx} returned something "
        f"that isn't a 2D list of integers. Got: {type(out).__name__}.\n\n"
        f"Return a list of rows, where each row is a list of integers (colors 0-9)."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle_id")
    parser.add_argument("model", help=f"One of: {', '.join(MODEL_DIR)}")
    parser.add_argument("paste_file")
    parser.add_argument("--iter", type=int, default=None)
    parser.add_argument("--label", action="store_true",
                        help="Research mode: when training pass rate=1.0, label outcome "
                             "against test ground truth and save to research/ corpus.")
    parser.add_argument("--hedge", action="store_true",
                        help="When training pass rate=1.0, save the current solve as "
                             "iter_N_first_solve and emit a hedge prompt path for a "
                             "fresh independent invocation. Use --hedge-result to "
                             "compare the second solve to the first.")
    parser.add_argument("--hedge-result", default=None,
                        help="Path to the hedge response paste (fresh invocation's "
                             "response). Compares its hand grid to the first solve's "
                             "code output and reports agreement.")
    parser.add_argument("--stateless", action="store_true",
                        help="When training pairs fail, also emit a self-contained "
                             "iter-N+1 prompt ready for stateless API submission. "
                             "The prompt includes seed structure + this iter's code "
                             "+ diagnosis, so no chat history is required to "
                             "continue iterating.")
    args = parser.parse_args()

    model_key = args.model.lower()
    if model_key not in MODEL_DIR:
        print(json.dumps({"error": f"unknown model {args.model}"}))
        sys.exit(1)

    puzzle_file = str(Path("evaluation") / f"{args.puzzle_id}.json")
    if not Path(puzzle_file).exists():
        legacy = f"puzzle_{args.puzzle_id}.json"
        if Path(legacy).exists():
            puzzle_file = legacy
        else:
            print(json.dumps({"error": f"puzzle file not found: {puzzle_file} or {legacy}"}))
            sys.exit(1)

    out_dir = Path("Model Results") / MODEL_DIR[model_key] / args.puzzle_id
    out_dir.mkdir(parents=True, exist_ok=True)

    n = args.iter if args.iter is not None else next_iter_n(out_dir)

    # Fresh iter 1 wipes any leftover iter_2+ files from a previous session
    # in this puzzle directory. Prevents cross-session pollution where stale
    # iter files confuse the regression detector (the prior iter looked at
    # for comparison must belong to the same chat session).
    if n == 1 and out_dir.exists():
        for stale in list(out_dir.iterdir()):
            if not (stale.is_file() and stale.name.startswith("iter_")):
                continue
            parts = stale.name.split("_")
            if len(parts) < 2:
                continue
            iter_n_str = parts[1]
            if iter_n_str.isdigit() and int(iter_n_str) > 1:
                stale.unlink()

    history_file = f"{args.puzzle_id}_history.json"
    if n == 1 and os.path.exists(history_file):
        os.remove(history_file)
        for ckpt in Path(".").glob(f"{args.puzzle_id}_checkpoint_pair_*.py"):
            ckpt.unlink()

    response = Path(args.paste_file).read_text()
    response_path = out_dir / f"iter_{n}_response.txt"
    response_path.write_text(response)

    code = extract_solve(response)
    if code is None:
        manifest = {
            "iter": n,
            "model": args.model,
            "puzzle_id": args.puzzle_id,
            "error": "no def solve() in response",
            "files": {"response": str(response_path)},
        }
        print(json.dumps(manifest, indent=2))
        sys.exit(1)

    code_path = out_dir / f"iter_{n}_response.py"
    code_path.write_text(code)
    Path("solution.py").write_text(code)

    hand_grid = extract_hand_grid(response)
    hand_grid_path = None
    hand_validation = None
    if hand_grid is not None:
        hand_grid_path = out_dir / f"iter_{n}_hand_grid.json"
        hand_grid_path.write_text(json.dumps(hand_grid))
        hand_validation = validate_hand_grid(hand_grid, puzzle_file)

    # Run validator
    result = subprocess.run(
        [sys.executable, "run_feedback.py", puzzle_file, "solution"],
        capture_output=True, text=True,
    )
    feedback_file = Path(f"feedback_{args.puzzle_id}.txt")
    if feedback_file.exists():
        feedback = feedback_file.read_text()
    else:
        feedback = (f"VALIDATOR ERROR (exit {result.returncode}):\n\n"
                    f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")

    prev_code_path = None
    if n > 1:
        candidate = out_dir / f"iter_{n - 1}_response.py"
        if candidate.exists():
            prev_code_path = str(candidate)

    diagnosis_block = compute_diagnosis(
        puzzle_file, "solution.py",
        prev_code_path=prev_code_path,
        current_code_path=str(code_path),
        iter_n=n,
    )
    if diagnosis_block:
        feedback = diagnosis_block + "\n\n" + feedback

    feedback_path = out_dir / f"iter_{n}_feedback.txt"
    feedback_path.write_text(feedback)

    verdict = "UNKNOWN"
    if "Verdict: SUBMIT" in feedback or "VERDICT: SUBMIT" in feedback:
        verdict = "SUBMIT"
    elif "DO NOT SUBMIT" in feedback:
        verdict = "DO NOT SUBMIT"

    code_test_result = validate_code_on_test(puzzle_file, "solution.py")

    summary = {
        "iter": n,
        "model": args.model,
        "puzzle_id": args.puzzle_id,
        "verdict": verdict,
        "hand_grid_validation": hand_validation,
        "code_test_result": code_test_result,
    }
    summary_path = out_dir / f"iter_{n}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    stateless_artifacts = {}
    if args.stateless:
        try:
            from seed_prompt import build_iteration_prompt
        except ImportError:
            stateless_artifacts = {"error": "seed_prompt module unavailable"}
        else:
            with open(puzzle_file) as f:
                puzzle_obj_s = json.load(f)
            # Compute training_pass_rate so we know if we even need an iter prompt
            train_pairs_s = puzzle_obj_s.get("train", [])
            try:
                spec_s = importlib.util.spec_from_file_location("_state_check", "solution.py")
                mod_s = importlib.util.module_from_spec(spec_s)
                spec_s.loader.exec_module(mod_s)
                pass_count_s = sum(
                    1 for p in train_pairs_s
                    if mod_s.solve(p["input"]) == p["output"]
                )
            except Exception:
                pass_count_s = 0
            if pass_count_s < len(train_pairs_s) and code_path.exists():
                # Strip the diagnosis block out of the just-written feedback.
                # It already has FEEDBACK SUMMARY + DIAGNOSIS at the top.
                diagnosis_only = feedback.split(
                    "================================================================================\n"
                    "VALIDATION SUMMARY\n"
                )[0].rstrip()
                next_iter_prompt = build_iteration_prompt(
                    puzzle_obj_s,
                    code_path.read_text(),
                    diagnosis_only,
                    iter_n=n + 1,
                )
                next_prompt_path = out_dir / f"iter_{n + 1}_stateless_prompt.txt"
                next_prompt_path.write_text(next_iter_prompt)
                stateless_artifacts["next_iter_prompt"] = str(next_prompt_path)
                stateless_artifacts["bytes"] = len(next_iter_prompt)
            else:
                stateless_artifacts["skipped"] = (
                    f"training_pass_rate={pass_count_s}/{len(train_pairs_s)} "
                    "(no next iter needed)"
                )

    hedge_artifacts = {}
    if args.hedge or args.hedge_result:
        try:
            puzzle_obj_h = json.load(open(puzzle_file))
            train_pairs_h = puzzle_obj_h.get("train", [])
            train_total_h = len(train_pairs_h)
            train_pass_h = 0
            spec_h = importlib.util.spec_from_file_location("_hedge_check", "solution.py")
            mod_h = importlib.util.module_from_spec(spec_h)
            spec_h.loader.exec_module(mod_h)
            for pair in train_pairs_h:
                try:
                    if mod_h.solve(pair["input"]) == pair["output"]:
                        train_pass_h += 1
                except Exception:
                    break
            train_pass_rate_h = train_pass_h / train_total_h if train_total_h else 0.0
        except Exception:
            train_pass_rate_h = 0.0

        if train_pass_rate_h == 1.0:
            seed_path = Path("Seed Prompts") / f"{args.puzzle_id}_seed.txt"
            if seed_path.exists():
                hedge_artifacts["seed_prompt"] = str(seed_path)
            hedge_artifacts["instructions"] = (
                "Training pass rate = 1.0. To hedge: paste the seed prompt "
                "above into a NEW chat session (not a continuation), then run "
                "paste_helper.py again with --hedge-result <path-to-second-paste>."
            )

            if args.hedge_result and Path(args.hedge_result).exists():
                second_response = Path(args.hedge_result).read_text()
                second_code = extract_solve(second_response)
                second_grid = extract_hand_grid(second_response)

                first_grid = None
                try:
                    first_grid = mod_h.solve(json.load(open(puzzle_file))["test"][0]["input"])
                except Exception:
                    pass

                if second_grid is None and second_code:
                    spec2 = importlib.util.spec_from_file_location("_hedge_sec", "/tmp/_hedge.py")
                    Path("/tmp/_hedge.py").write_text(second_code)
                    spec2 = importlib.util.spec_from_file_location("_hedge_sec", "/tmp/_hedge.py")
                    mod2 = importlib.util.module_from_spec(spec2)
                    try:
                        spec2.loader.exec_module(mod2)
                        second_grid = mod2.solve(json.load(open(puzzle_file))["test"][0]["input"])
                    except Exception:
                        second_grid = None

                agreement = None
                if first_grid is not None and second_grid is not None:
                    if (len(first_grid) == len(second_grid)
                            and all(len(first_grid[r]) == len(second_grid[r]) for r in range(len(first_grid)))):
                        diff = sum(
                            1 for r in range(len(first_grid))
                            for c in range(len(first_grid[0]))
                            if first_grid[r][c] != second_grid[r][c]
                        )
                        total = len(first_grid) * len(first_grid[0])
                        agreement = {
                            "agree": diff == 0,
                            "differing_cells": diff,
                            "total_cells": total,
                        }
                hedge_artifacts["agreement"] = agreement
        else:
            hedge_artifacts["skipped"] = (
                f"hedge requires training_pass_rate=1.0 (got {train_pass_rate_h:.2f})"
            )

    research_artifacts = {}
    if args.label:
        try:
            from research_mode import (
                append_calibration_row,
                label_outcome,
                save_corpus_artifacts,
                write_final_label,
            )
        except ImportError:
            research_artifacts = {"error": "research_mode module unavailable"}
        else:
            puzzle_obj = json.load(open(puzzle_file))
            train_pairs = puzzle_obj.get("train", [])
            train_total = len(train_pairs)
            train_pass = 0
            try:
                spec = importlib.util.spec_from_file_location("_train_check", "solution.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for pair in train_pairs:
                    try:
                        if mod.solve(pair["input"]) == pair["output"]:
                            train_pass += 1
                    except Exception:
                        break
            except Exception:
                train_pass = 0

            train_pass_rate = train_pass / train_total if train_total else 0.0

            if train_pass_rate == 1.0:
                label_data = label_outcome(puzzle_file, "solution.py")
                research_artifacts["label"] = label_data.get("label")
                research_artifacts["test_diff_count"] = label_data.get("test_diff_count")

                final_label_path = write_final_label(
                    out_dir, label_data, n, train_pass_rate
                )
                research_artifacts["final_label"] = final_label_path

                prev_iter_data = None
                prev_n = n - 1
                if prev_n >= 1:
                    prev_summary_path = out_dir / f"iter_{prev_n}_summary.json"
                    prev_code_path = out_dir / f"iter_{prev_n}_response.py"
                    if prev_summary_path.exists() and prev_code_path.exists():
                        prev_iter_data = {
                            "iter": prev_n,
                            "code_path": str(prev_code_path),
                            "summary": json.loads(prev_summary_path.read_text()),
                        }

                written = save_corpus_artifacts(
                    args.puzzle_id, MODEL_DIR[model_key], n,
                    str(code_path), str(feedback_path),
                    label_data, prev_iter_data=prev_iter_data,
                )
                research_artifacts.update({"corpus": written})

                cal_path = append_calibration_row(
                    args.puzzle_id, MODEL_DIR[model_key], n,
                    train_pass_rate, label_data,
                )
                research_artifacts["calibration_csv"] = cal_path
            else:
                research_artifacts["skipped"] = (
                    f"training_pass_rate={train_pass_rate:.2f} (need 1.0 to label)"
                )

    manifest = {
        "iter": n,
        "model": args.model,
        "puzzle_id": args.puzzle_id,
        "verdict": verdict,
        "hand_grid_validation": hand_validation,
        "code_test_result": code_test_result,
        "files": {
            "response": str(response_path),
            "code": str(code_path),
            "feedback": str(feedback_path),
            "summary": str(summary_path),
            **({"hand_grid": str(hand_grid_path)} if hand_grid_path else {}),
        },
        **({"research": research_artifacts} if research_artifacts else {}),
        **({"hedge": hedge_artifacts} if hedge_artifacts else {}),
        **({"stateless": stateless_artifacts} if stateless_artifacts else {}),
    }
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
