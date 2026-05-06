"""
Competition validator for ARC-AGI:
  Submit gate: Training 3/3 (solve reproduces every training output exactly)
  Submission:  solve(test_input)

If training fails, generate substrate feedback per failed training pair, plus a
test self-inspection block so the LLM sees what its current code would submit.
Also includes confirmation blocks for passing pairs so the LLM is anchored on
what its current rule already gets right and does NOT regress when fixing
the failing pairs.

Iteration history is persisted to <puzzle_id>_history.json and rendered at the
top of every feedback file so the LLM sees how its understanding evolved.

Usage:
  1. Save the LLM's solve() function to a file (default: solution.py)
  2. python run_feedback.py <puzzle_file.json> [solution_module]

Examples:
  python run_feedback.py puzzle_8f3a5a89.json
  python run_feedback.py puzzle_135a2760.json solution
"""

import json
import importlib
import re
import sys
from pathlib import Path

from complete_substrate_feedback import (
    generate_complete_substrate_feedback,
    generate_test_self_inspection,
)
from transformation_grid import generate_transformation_grid


def derive_puzzle_id(puzzle_file: str) -> str:
    """Extract puzzle ID from filename (e.g. 'puzzle_8f3a5a89.json' -> '8f3a5a89').
    Falls back to the bare stem if the 'puzzle_' prefix is absent."""
    stem = Path(puzzle_file).stem
    m = re.match(r'^puzzle_(.+)$', stem)
    return m.group(1) if m else stem



def checkpoint_path(puzzle_id, pair_num):
    return Path(f"{puzzle_id}_checkpoint_pair_{pair_num}.py")


def save_checkpoint(puzzle_id, pair_num, solution_module):
    src = Path(f"{solution_module}.py").read_text()
    checkpoint_path(puzzle_id, pair_num).write_text(src)


def load_checkpoint(puzzle_id, pair_num):
    p = checkpoint_path(puzzle_id, pair_num)
    return p.read_text() if p.exists() else None


def has_passed_before(pair_idx_zero_based, prior_history):
    return any(entry["pairs"][pair_idx_zero_based] for entry in prior_history)


def render_regression_block(pair_number, checkpoint_source):
    out = "=" * 80 + "\n"
    out += f"REGRESSION ALERT - PAIR {pair_number}\n"
    out += "=" * 80 + "\n\n"
    out += (
        f"Pair {pair_number} PASSED in a previous iteration with the code below,\n"
        f"and your CURRENT code FAILS it. You broke working logic.\n\n"
        f"Diff your current solve() against this checkpoint. The mechanism that\n"
        f"made Pair {pair_number} pass needs to come back - preserved verbatim if\n"
        f"possible, or carefully merged with whatever fixes the other failing\n"
        f"pairs. Do not silently rewrite logic that was already working.\n\n"
    )
    out += f"CHECKPOINT (last solve() that passed Pair {pair_number}):\n\n"
    out += "```python\n"
    out += checkpoint_source.rstrip() + "\n"
    out += "```\n"
    return out


def code_reminder(passing_pairs, failing_pairs, regressed_pairs):
    """Reminder block - varies based on which pairs pass / fail."""
    pass_list = ", ".join(str(i) for i in passing_pairs) if passing_pairs else "none"
    fail_list = ", ".join(str(i) for i in failing_pairs) if failing_pairs else "none"
    regressed_list = ", ".join(str(i) for i in regressed_pairs) if regressed_pairs else "none"
    regression_section = ""
    if regressed_pairs:
        regression_section = (
            f"- Pair(s) REGRESSED: {regressed_list}  "
            f"<- Were passing previously. A REGRESSION ALERT block below echoes\n"
            f"  the last solve() that passed each. Diff your current code against\n"
            f"  it before rewriting; restore the mechanism that worked.\n"
        )
    return f"""\
================================================================================
NEXT STEP: UPDATE YOUR PYTHON
================================================================================

Read the per-pair diagnostics below, identify what your code did wrong on each
failed pair, then return an UPDATED `def solve(input_grid):` function.

You MUST update your Python. Do NOT respond with prose only, hand-computed
grids, or partial pseudocode. We run your code; we do not read narratives.
If your response does not contain a `def solve(input_grid):` function, the
iteration is invalid and you receive no further feedback.

CURRENT STATUS:
- Pair(s) PASSING: {pass_list}  <- MUST CONTINUE TO PASS. Do not regress.
- Pair(s) FAILING: {fail_list}  <- Fix these.
{regression_section}
CRITICAL: Your updated code MUST keep producing correct output for the passing
pair(s) AND fix the failing pair(s). If your fix breaks a previously passing
pair, the score does not improve - you only swap which pair fails.

REGRESSION DETECTOR: Before submitting, mentally diff your new solve() against
your previous one. For each pair currently passing, ask: "is the logic that
made it pass still intact?" If you cannot point to the specific lines that
preserve that pair's behavior, your edit likely has a regression bug.

CODE PITFALLS - common bugs when translating reasoning to Python. Scan each
of these against your code before submitting.

1) CLUSTER PROPERTY TESTED PER CELL (instead of computed once at cluster level)
   Wrong:  for r, c in cluster:
              if r == 0 or c == 0 or r == H-1 or c == W-1:
                  is_edge = True
           # bug: only edge-cells of the cluster trigger this; middle cells
           # of a cluster that touches edge fail the per-cell test.
   Right:  is_edge = any(r == 0 or c == 0 or r == H-1 or c == W-1
                         for r, c in cluster)
           if is_edge:
              for r, c in cluster:
                  edge_cells.add((r, c))

2) 4-CONN vs 8-CONN ADJACENCY (default is 4; halo/expansion often needs 8)
   4-conn: [(-1, 0), (1, 0), (0, -1), (0, 1)]  # cardinal only
   8-conn: above + [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # cardinal + diagonal
   Tip: BFS through walls usually wants 4-conn. Halo painting around a region
   usually wants 8-conn. Pick per rule - don't default both to 4-conn.

3) 8-NEIGHBORHOOD ITERATION (the diagonal sandwich)
   Wrong:  for dr in [-1, 1]:
              for dc in [-1, 1]: ...   # MISSES the 4 cardinals
   Wrong:  for dr in [-1, 0, 1]:
              for dc in [-1, 0, 1]: ...   # INCLUDES self at (0, 0)
   Right:  for dr in [-1, 0, 1]:
              for dc in [-1, 0, 1]:
                  if dr == 0 and dc == 0: continue
                  ...

4) HARDCODED GRID DIMENSIONS / INDICES
   Wrong:  if r == 15 or c == 11: ...   # only works on the test grid shape
   Right:  H, W = len(grid), len(grid[0])
           if r == H - 1 or c == W - 1: ...

5) MUTATING THE GRID WHILE ITERATING IT
   Wrong:  for r, c in cells:
              if grid[r][c] == 1: grid[r][c] = 8   # later reads see 8 now
   Right:  output = [row[:] for row in grid]
           for r, c in cells:
              if grid[r][c] == 1: output[r][c] = 8   # read from grid, write to output

6) ALIASING / FORGETTING DEEP COPY
   Wrong:  grid = input_grid; grid[r][c] = 8   # corrupts caller's input_grid
   Right:  grid = [row[:] for row in input_grid]

7) BINARY REDUCTION LOSES MULTI-COLOR INFO
   When a panel / region has TWO OR MORE non-background colors, reducing
   to 1-bit `is_fg` (most common) vs `is_bg` (everything else) discards
   the other color's positional information.
   Wrong:  fg = Counter(non_bg_vals).most_common(1)[0][0]
           bits = [[1 if v == fg else 0 for v in row] for row in block]
           # Now you cannot distinguish color X from color Y when both are non-bg.
           # Period/symmetry detected on `bits` will collapse to a single color.
   Right:  Detect period/structure over the SEQUENCE of values, not over a
           binary mask. For each tile position, take the most common VALUE
           (not bit) across all its repeats. Or run the detector once per
           non-bg color independently and merge the results.

REQUIREMENTS for your next response:
- MUST contain a `def solve(input_grid):` function. We run your code; we do
  not read hand-computed grids. Responses without a solve() function cannot
  be validated and you receive no further feedback.
- The function must work on grids of ANY size - do not hardcode dimensions,
  row indices, or column indices. The validator runs your code on grids of
  different sizes (the training pairs and the test input each have their own
  shape).
- Return a 2D list of integers (colors 0-9).

DO NOT manually write out a test output grid. The grid that gets submitted is
solve(test_input), computed by us. Your job is to update the algorithm.

"""


def render_passing_pair(pair_number, input_grid, output_grid):
    """
    Confirmation block for a passing pair - reminds the LLM that its current
    rule produces this exact output, which matches expected. The transformation
    grid encoding is included as the canonical anchor.
    """
    out = "=" * 80 + "\n"
    out += f"PAIR {pair_number} - PASSING (preserve this behavior)\n"
    out += "=" * 80 + "\n\n"
    out += "Your code already produces the correct output for this pair. The\n"
    out += "transformation rule applied below is what your algorithm got right.\n"
    out += "Whatever you change next must keep producing this exact output here.\n\n"

    out += "INPUT:\n"
    for row in input_grid:
        out += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    out += "\nCORRECT OUTPUT (your code matches this):\n"
    for row in output_grid:
        out += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"

    trans, _ = generate_transformation_grid(input_grid, output_grid)
    out += "\nTRANSFORMATION RULE (correct):\n"
    out += "Symbols: . = unchanged, = = preserved, + = activated, - = removed\n\n"
    for row in trans:
        # Pad each symbol to 2 chars so columns visually align with data grids
        out += "[" + ", ".join(f"{s:>2}" for s in row) + "]\n"

    return out


def load_history(history_file):
    p = Path(history_file)
    if p.exists():
        return json.loads(p.read_text())
    return []


def save_history(history_file, history):
    Path(history_file).write_text(json.dumps(history, indent=2))


def render_history(past_history, current_iter):
    if not past_history:
        return ""
    lines = ["=" * 80, "ITERATION HISTORY", "=" * 80, ""]
    for entry in past_history:
        marks = "  ".join(
            f"Pair {i+1} {'PASS' if p else 'FAIL'}"
            for i, p in enumerate(entry["pairs"])
        )
        lines.append(
            f"Iter {entry['iter']}: {marks}  ({entry['passed']}/{entry['total']})"
        )
    lines.append(f"Iter {current_iter} (current): see full diagnostics below")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_feedback.py <puzzle_file.json> [solution_module]")
        print("Example: python run_feedback.py puzzle_8f3a5a89.json")
        sys.exit(1)

    puzzle_file = sys.argv[1]
    solution_module = sys.argv[2] if len(sys.argv) > 2 else "solution"
    puzzle_id = derive_puzzle_id(puzzle_file)
    history_file = f"{puzzle_id}_history.json"
    out_file = f"feedback_{puzzle_id}.txt"

    solve = importlib.import_module(solution_module).solve

    with open(puzzle_file) as f:
        puzzle = json.load(f)

    history = load_history(history_file)
    current_iter = len(history) + 1

    print("=" * 80)
    print(f"ITERATION {current_iter} - TRAINING VALIDATION (puzzle {puzzle_id})")
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

    test_input = puzzle["test"][0]["input"]
    solve_test_output = solve(test_input)

    passing_pairs = [i for i, p, _, _ in train_results if p]
    failing_pairs = [i for i, p, _, _ in train_results if not p]

    # Save checkpoint for each currently-passing pair so future regressions can
    # echo the last solve() that worked.
    for i, passed, _, _ in train_results:
        if passed:
            save_checkpoint(puzzle_id, i, solution_module)

    # A pair is REGRESSED if it failed this iter but passed in any prior iter.
    regressed_pairs = [
        i for i, passed, _, _ in train_results
        if not passed and has_passed_before(i - 1, history)
    ]

    if all_train_pass:
        verdict = "SUBMIT"
        header = (
            "READY TO SUBMIT: training 3/3 pass. The code's output on test input "
            "is our hypothesis. No more iteration needed."
        )
    else:
        verdict = "DO NOT SUBMIT"
        header = (
            f"Your transformation rule did not generalize across all training "
            f"pairs (failed on pair(s) {failing_pairs}). Update your Python."
        )
    print("\nVERDICT:", verdict)
    print(header)

    history.append({
        "iter": current_iter,
        "pairs": [bool(p) for _, p, _, _ in train_results],
        "passed": train_pass_count,
        "total": len(train_results),
        "verdict": verdict,
    })
    save_history(history_file, history)

    history_block = render_history(history[:-1], current_iter)

    summary = (
        "=" * 80 + "\n"
        "VALIDATION SUMMARY\n"
        + "=" * 80 + "\n\n"
        + f"Iteration: {current_iter}\n"
        + f"Verdict: {verdict}\n"
        + f"Training: {train_pass_count}/{len(train_results)} pairs pass\n\n"
        + header + "\n\n"
    )

    reminder = "" if all_train_pass else code_reminder(
        passing_pairs, failing_pairs, regressed_pairs
    )

    feedback_blocks = [history_block + summary + reminder] if history_block else [summary + reminder]

    # Order: passing pairs first (anchor what's right), then regression alerts
    # (with checkpoint code), then failing-pair diagnostics.
    for i, passed, pair, actual in train_results:
        if passed and not all_train_pass:
            feedback_blocks.append(render_passing_pair(i, pair["input"], pair["output"]))

    for i in regressed_pairs:
        ckpt = load_checkpoint(puzzle_id, i)
        if ckpt:
            feedback_blocks.append(render_regression_block(i, ckpt))

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
    with open(out_file, "w") as f:
        f.write(combined)

    print(f"\nSaved {len(combined):,} chars to {out_file}")
    print(f"History persisted to {history_file} ({len(history)} iter(s))")


if __name__ == "__main__":
    main()
