"""
Competition validator for ARC-AGI:
  Submit gate: Training 3/3 (solve reproduces every training output exactly)
  Submission:  solve(test_input)

If training fails, generate substrate feedback per failed training pair, plus a
test self-inspection block so the LLM sees what its current code would submit.

Usage:
  1. Save the LLM's solve() function to a file (e.g. gpt_solution.py)
  2. Edit PUZZLE_FILE / SOLUTION_MODULE / OUT_FILE below
  3. python run_feedback.py
"""

import json
import importlib

from complete_substrate_feedback import (
    generate_complete_substrate_feedback,
    generate_test_self_inspection,
)

PUZZLE_FILE = "puzzle.json"          # ARC puzzle JSON
SOLUTION_MODULE = "gpt_solution"     # module exposing solve(input_grid)
OUT_FILE = "feedback.txt"            # combined feedback output


def main():
    solve = importlib.import_module(SOLUTION_MODULE).solve

    with open(PUZZLE_FILE) as f:
        puzzle = json.load(f)

    # Phase 1: training validation
    print("=" * 80)
    print("TRAINING VALIDATION")
    print("=" * 80)
    train_results = []
    for i, pair in enumerate(puzzle["train"], 1):
        actual = solve(pair["input"])
        expected = pair["output"]
        passed = actual == expected
        train_results.append((i, passed, pair, actual))
        print(f"  Pair {i}: {'PASS' if passed else 'FAIL'}")

    train_pass_count = sum(1 for _, p, _, _ in train_results if p)
    all_train_pass = train_pass_count == len(train_results)
    print(f"\nTraining: {train_pass_count}/{len(train_results)}")

    # Always run code on test input - this is the hypothesis we'd submit
    test_input = puzzle["test"][0]["input"]
    solve_test_output = solve(test_input)

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    if all_train_pass:
        verdict = "SUBMIT"
        header = (
            "READY TO SUBMIT: training 3/3 pass. The code's output on test input "
            "is our hypothesis. No more iteration needed."
        )
    else:
        failing = [i for i, p, _, _ in train_results if not p]
        verdict = "DO NOT SUBMIT"
        header = (
            f"Your transformation rule did not generalize across all training "
            f"pairs (failed on pair(s) {failing}). Iterate."
        )
    print(verdict)
    print(header)

    # Build feedback file
    summary = (
        "=" * 80 + "\n"
        "VALIDATION SUMMARY\n"
        + "=" * 80 + "\n\n"
        + f"Verdict: {verdict}\n"
        + f"Training: {train_pass_count}/{len(train_results)} pairs pass\n\n"
        + header + "\n\n"
    )

    feedback_blocks = [summary]
    for i, passed, pair, actual in train_results:
        if not passed:
            feedback_blocks.append(
                generate_complete_substrate_feedback(
                    pair["input"], pair["output"], actual, pair_number=i
                )
            )

    if not all_train_pass:
        feedback_blocks.append(
            generate_test_self_inspection(test_input, solve_test_output)
        )

    combined = "\n\n".join(feedback_blocks)
    with open(OUT_FILE, "w") as f:
        f.write(combined)

    print(f"\nSaved {len(combined):,} chars of feedback to {OUT_FILE}")
    print(f"Failed train pairs: {[i for i, p, _, _ in train_results if not p]}")


if __name__ == "__main__":
    main()
