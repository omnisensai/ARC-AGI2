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


def extract_rule(text):
    """Extract the STATED_RULE: <sentence> line that the seed prompt requires.

    Returns the rule sentence (without the STATED_RULE: prefix) or None if not
    present. The rule is captured verbatim from the model's response so it can
    be replayed into a fresh-refinement prompt without paraphrasing.
    """
    # Look for STATED_RULE on its own line (with or without leading markdown
    # markers like "* ", "- ", "**"). Stop at the next blank line, code fence,
    # or another all-caps heading-looking line.
    pattern = re.compile(
        r"^\s*(?:[-*]\s+)?\**\s*STATED_RULE\s*\**\s*:\s*\**\s*(.+?)\s*$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return None
    rule = m.group(1).strip()
    # Strip stray markdown emphasis around the sentence itself.
    rule = rule.strip("*_`").strip()
    return rule or None


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
    """Run solve() against every test pair that has ground-truth output.

    Returns aggregate stats across all test pairs plus a per-pair breakdown.
    Some ARC puzzles ship multiple test inputs (13e47133 has 2); the framework
    previously only looked at puzzle['test'][0] and silently ignored the rest,
    which caused TRUE_SOLVE / FALSE_CONFIDENT_SUBMIT labels to be wrong for
    multi-test puzzles.
    """
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    test_pairs = [t for t in puzzle.get("test", []) if "output" in t]
    if not test_pairs:
        return None
    spec = importlib.util.spec_from_file_location("_iter_sol", solution_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return {"status": "error", "msg": str(e)}

    per_pair = []
    total_diffs = 0
    total_cells = 0
    for idx, tpair in enumerate(test_pairs):
        truth = tpair["output"]
        try:
            out = mod.solve(tpair["input"])
        except Exception as e:
            per_pair.append({"idx": idx, "status": "error", "msg": str(e)})
            continue
        if not isinstance(out, list) or not out or not isinstance(out[0], list):
            per_pair.append({"idx": idx, "status": "error", "msg": "solve() did not return 2D list"})
            continue
        if len(out) != len(truth) or any(
            len(out[r]) != len(truth[r]) for r in range(len(truth))
        ):
            per_pair.append({"idx": idx, "status": "dim_mismatch",
                             "got": f"{len(out)}x{len(out[0])}"})
            continue
        diffs = sum(
            1 for r in range(len(truth)) for c in range(len(truth[0]))
            if out[r][c] != truth[r][c]
        )
        total = len(truth) * len(truth[0])
        per_pair.append({"idx": idx, "diffs": diffs, "total": total,
                         "matches": diffs == 0})
        total_diffs += diffs
        total_cells += total

    # Status surfaces if any per-pair errored; otherwise aggregate.
    any_error = any(p.get("status") == "error" for p in per_pair)
    any_dim = any(p.get("status") == "dim_mismatch" for p in per_pair)
    if any_error:
        return {"status": "error",
                "msg": next(p["msg"] for p in per_pair if p.get("status") == "error"),
                "per_pair": per_pair}
    if any_dim:
        return {"status": "dim_mismatch",
                "got": next(p["got"] for p in per_pair if p.get("status") == "dim_mismatch"),
                "per_pair": per_pair}
    return {
        "matches": total_diffs == 0,
        "diffs": total_diffs,
        "total": total_cells,
        "per_pair": per_pair,
        "num_test_pairs": len(per_pair),
    }


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


def _format_ground_truth_check(code_test_result):
    """When training passes 3/3, surface whether code's test output matches truth.

    Returns None if no ground truth is available (real competition mode — puzzle
    file has no test[0]['output']) or if validate_code_on_test errored. This
    block is appended AFTER iteration is already over (training passed → no
    further model call), so it never influences a model — it's strictly a
    human-facing label for research/practice runs.

    Thresholds match the constitution:
      - exact match → TRUE_SOLVE
      - ≤20 diff cells → NEAR_MISS
      - >20 diff cells → FALSE_CONFIDENT_SUBMIT
    """
    if code_test_result is None:
        return None
    if code_test_result.get("status") == "error":
        return None
    if code_test_result.get("status") == "dim_mismatch":
        return (
            "=" * 80 + "\n"
            "GROUND TRUTH CHECK\n"
            + "=" * 80 + "\n\n"
            f"Label: FALSE_CONFIDENT_SUBMIT (dimension mismatch)\n"
            f"Code's test output is {code_test_result.get('got', '?')} but ground "
            f"truth has different dimensions.\n"
        )
    if "matches" not in code_test_result:
        return None
    diffs = code_test_result["diffs"]
    total = code_test_result["total"]
    correct = total - diffs
    pct = 100.0 * correct / total if total else 0.0
    if diffs == 0:
        label = "TRUE_SOLVE"
        verdict_line = "Code's test output exactly matches ground truth on all test pairs."
    elif diffs <= 20:
        label = "NEAR_MISS"
        verdict_line = (
            f"Off by {diffs} cells (≤20 threshold). Submitted answer is "
            f"close but not exact."
        )
    else:
        label = "FALSE_CONFIDENT_SUBMIT"
        verdict_line = (
            f"Off by {diffs} cells (>20 threshold). Training passed but the "
            f"rule generalizes wrong — high-value corpus row."
        )

    per_pair_lines = []
    per_pair = code_test_result.get("per_pair") or []
    if len(per_pair) > 1:
        per_pair_lines.append("")
        for p in per_pair:
            if p.get("matches"):
                per_pair_lines.append(f"  Test pair {p['idx']}: PASS ({p['total']} cells)")
            else:
                d, t = p["diffs"], p["total"]
                per_pair_lines.append(
                    f"  Test pair {p['idx']}: off by {d}/{t} ({100.0*(t-d)/t:.1f}% correct)"
                )

    return (
        "=" * 80 + "\n"
        "GROUND TRUTH CHECK\n"
        + "=" * 80 + "\n\n"
        f"Label: {label}\n"
        f"Test cells correct: {correct}/{total} ({pct:.1f}%)"
        + (f" across {len(per_pair)} test pairs" if len(per_pair) > 1 else "")
        + "\n"
        f"{verdict_line}\n"
        + "\n".join(per_pair_lines)
        + ("\n" if per_pair_lines else "")
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
    parser.add_argument("--fresh-refine", action="store_true",
                        help="When training pairs partially pass (>=1 PASS and >=1 "
                             "FAIL), emit a fresh-refinement prompt for a NEW chat "
                             "session. The prompt contains prior code + prior "
                             "STATED_RULE + per-pair PASS/FAIL status + "
                             "judge-then-repair instructions. The model first picks "
                             "A (rule correct, patch code) or B (rule wrong, replace "
                             "abstraction). Comp-clean: leaks no info derived from "
                             "test ground truth.")
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

    rule = extract_rule(response)
    rule_path = None
    if rule:
        rule_path = out_dir / f"iter_{n}_rule.txt"
        rule_path.write_text(rule + "\n")

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

    verdict = "UNKNOWN"
    if "Verdict: SUBMIT" in feedback or "VERDICT: SUBMIT" in feedback:
        verdict = "SUBMIT"
    elif "DO NOT SUBMIT" in feedback:
        verdict = "DO NOT SUBMIT"

    code_test_result = validate_code_on_test(puzzle_file, "solution.py")

    # When training passes (Verdict: SUBMIT) and the puzzle file has test
    # ground truth available, append the TRUE_SOLVE / NEAR_MISS /
    # FALSE_CONFIDENT_SUBMIT label. Safe: iteration is over by this point, so
    # showing ground truth doesn't feed back into any model call. In real
    # competition the puzzle file won't carry test['output'] and this is a
    # no-op.
    if verdict == "SUBMIT":
        gt_block = _format_ground_truth_check(code_test_result)
        if gt_block:
            feedback = feedback.rstrip() + "\n\n" + gt_block

    feedback_path = out_dir / f"iter_{n}_feedback.txt"
    feedback_path.write_text(feedback)

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

    fresh_refine_artifacts = {}
    if args.fresh_refine:
        try:
            from seed_prompt import build_fresh_refine_prompt
        except ImportError:
            fresh_refine_artifacts = {"error": "seed_prompt module unavailable"}
        else:
            puzzle_obj_fr = json.load(open(puzzle_file))
            train_pairs_fr = puzzle_obj_fr.get("train", [])
            pair_status = {}
            try:
                spec_fr = importlib.util.spec_from_file_location("_fr_check", "solution.py")
                mod_fr = importlib.util.module_from_spec(spec_fr)
                spec_fr.loader.exec_module(mod_fr)
                for idx, pair in enumerate(train_pairs_fr, 1):
                    try:
                        out_fr = mod_fr.solve(pair["input"])
                    except Exception as e:
                        pair_status[idx] = f"ERROR ({type(e).__name__})"
                        continue
                    truth = pair["output"]
                    if out_fr == truth:
                        pair_status[idx] = "PASS"
                    else:
                        h_t = len(truth)
                        w_t = len(truth[0]) if truth else 0
                        if (not isinstance(out_fr, list) or len(out_fr) != h_t
                                or any(len(out_fr[r]) != w_t for r in range(h_t))):
                            pair_status[idx] = "FAIL (dimension mismatch)"
                        else:
                            d = sum(1 for r in range(h_t) for c in range(w_t)
                                    if out_fr[r][c] != truth[r][c])
                            pair_status[idx] = f"FAIL ({d}/{h_t*w_t} cells wrong)"
            except Exception as e:
                fresh_refine_artifacts["error"] = f"could not evaluate code: {e}"

            pass_n = sum(1 for s in pair_status.values() if s == "PASS")
            fail_n = sum(1 for s in pair_status.values()
                         if s.startswith("FAIL") or s.startswith("ERROR"))

            if not pair_status:
                fresh_refine_artifacts.setdefault(
                    "skipped", "could not evaluate code on training pairs"
                )
            elif pass_n == 0:
                fresh_refine_artifacts["skipped"] = (
                    f"no training pair passes ({pass_n}/{len(train_pairs_fr)}); "
                    "use --stateless for iteration prompt instead"
                )
            elif fail_n == 0:
                fresh_refine_artifacts["skipped"] = (
                    f"all training pairs pass ({pass_n}/{len(train_pairs_fr)}); "
                    "use --hedge instead"
                )
            elif rule is None:
                fresh_refine_artifacts["skipped"] = (
                    "no STATED_RULE: line found in response. Fresh refinement "
                    "requires the model's own stated rule to feed back into "
                    "the new prompt. Re-run iter 1 with the updated seed "
                    "prompt that requires STATED_RULE."
                )
            else:
                # Gather any rules that have already been tried and rejected
                # on this puzzle. Looks at iter_*_rule.txt files in this dir
                # other than the current iter — those represent previous
                # rule statements the model has already proposed.
                rejected = []
                for prev_rule_file in sorted(out_dir.glob("iter_*_rule.txt")):
                    if prev_rule_file == rule_path:
                        continue
                    txt = prev_rule_file.read_text().strip()
                    if txt and txt != rule:
                        rejected.append(txt)
                fresh_prompt = build_fresh_refine_prompt(
                    puzzle_obj_fr,
                    prior_code=code_path.read_text(),
                    prior_rule=rule,
                    pair_status=pair_status,
                    rejected_rules=rejected or None,
                )
                fresh_prompt_path = out_dir / f"iter_{n + 1}_fresh_refine_prompt.txt"
                fresh_prompt_path.write_text(fresh_prompt)
                fresh_refine_artifacts["next_prompt"] = str(fresh_prompt_path)
                fresh_refine_artifacts["bytes"] = len(fresh_prompt)
                fresh_refine_artifacts["pair_status"] = pair_status
                fresh_refine_artifacts["rejected_rules_count"] = len(rejected)

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
            **({"rule": str(rule_path)} if rule_path else {}),
        },
        **({"stated_rule": rule} if rule else {}),
        **({"research": research_artifacts} if research_artifacts else {}),
        **({"hedge": hedge_artifacts} if hedge_artifacts else {}),
        **({"stateless": stateless_artifacts} if stateless_artifacts else {}),
        **({"fresh_refine": fresh_refine_artifacts} if fresh_refine_artifacts else {}),
    }
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
