"""
Seed prompt generator (iter-1 only).

Replaces the v6 substrate prompt for iter-1. The substrate prompt's transformation
grids and heavy heuristics drowned the model in noise without consistently
helping (data showed identical results with/without transformation grids on
13e47133). The seed prompt instead:

  - Lists training pairs as input/output only (no transformation symbols)
  - Provides a structured-CoT scaffold (rule -> code -> trace -> apply) instead
    of heuristic TIPS
  - Keeps the dual-output requirement (def solve + TEST_OUTPUT) since
    code-as-output appears to be doing real work
  - Stays under ~3KB for typical 3-pair puzzles

Iter-N feedback (paste_helper.py + feedback_diagnostics.py) is where the
framework's intelligence lives. The seed prompt is intentionally minimal.

Usage:
    python seed_prompt.py evaluation/13e47133.json [out_path]
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def format_grid(grid: List[List[int]]) -> str:
    return "\n".join(str(row) for row in grid)


COT_SCAFFOLD = """\
================================================================================
HOW TO APPROACH
================================================================================

Work through the puzzle in this order:

1. Identify the transformation rule from the training pairs.
   State it in plain English, then in pseudocode.

2. Write `def solve(input_grid):` that implements the rule.

3. For each training pair, mentally trace your code on the pair's input.
   - State your code's output for that pair (in your reasoning, not in the
     final output block).
   - Compare to the expected output.
   - If they don't match, REVISE your code in step 2 before submitting.
   Do not submit code that you cannot mentally trace as matching every
   training pair.

4. Apply your code to the test input. The result goes in TEST_OUTPUT below.
"""


OUTPUT_FORMAT = """\
================================================================================
OUTPUT FORMAT (required)
================================================================================

Your response must include BOTH a `def solve(input_grid):` function AND a
hand-written TEST_OUTPUT grid:

```python
def solve(input_grid):
    # ...
    return output_grid
```

TEST_OUTPUT = [
    [...row 0 values...],
    ...
]

Requirements:
- The function must work on grids of any size (do not hardcode dimensions).
- Return a 2D list of integers (colors 0-9).
- TEST_OUTPUT must be the result of solve(test_input).
"""


def generate_seed_prompt(puzzle: Dict[str, Any]) -> str:
    parts = [
        "You are an ARC-AGI solver.",
        "",
        "Each puzzle gives you a small set of input -> output training pairs.",
        "Your job is to identify the transformation rule that produces every",
        "output from its input, then apply that rule to the test input.",
        "",
    ]

    for idx, pair in enumerate(puzzle["train"], 1):
        parts.append("=" * 80)
        parts.append(f"TRAINING PAIR {idx}")
        parts.append("=" * 80)
        parts.append("")
        parts.append("INPUT:")
        parts.append(format_grid(pair["input"]))
        parts.append("")
        parts.append("OUTPUT:")
        parts.append(format_grid(pair["output"]))
        parts.append("")

    parts.append(COT_SCAFFOLD)

    if puzzle.get("test"):
        parts.append("=" * 80)
        parts.append("TEST INPUT")
        parts.append("=" * 80)
        parts.append("")
        parts.append(format_grid(puzzle["test"][0]["input"]))
        parts.append("")

    parts.append(OUTPUT_FORMAT)
    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("usage: python seed_prompt.py <puzzle.json> [out_path]", file=sys.stderr)
        sys.exit(1)

    puzzle_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    puzzle = json.loads(puzzle_path.read_text())
    prompt = generate_seed_prompt(puzzle)

    if out_path:
        out_path.write_text(prompt)
        print(f"wrote {len(prompt):,} chars to {out_path}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
