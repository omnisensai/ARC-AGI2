"""
Seed prompt generator (iter-1) and iteration prompt builder (iter-N+1).

Iter 1 seed prompt: minimal — task line, training pairs, test input, a single
CoT sentence, mandatory output format. Used for fresh chat sessions OR
stateless iter-1 API calls.

Iter N+1 iteration prompt: same seed structure + the model's prior code +
the diagnosis block + "update solve()" instruction. Self-contained for
stateless API calls (no chat history needed).

Usage:
    python seed_prompt.py evaluation/13e47133.json [out_path]
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


TASK_STATEMENT = (
    "Solve this ARC-AGI puzzle. Identify the transformation rule from the "
    "training pairs and write a Python `def solve(input_grid):` function "
    "that generalizes to ALL training pairs and the test input."
)


PER_PAIR_ANALYSIS = """\
Analyze this pair:
- Anchor cells (unique seeds, single markers, distinctive objects):
- Barriers (walls, lines, obstacles):
- Adjacency that the rule uses: 4-connectivity or 8-connectivity?
- Your hypothesis for the rule (one sentence):
- Python sketch for this pair (a partial `solve()` that handles this pair):
"""


OUTPUT_FORMAT = """\
================================================================================
MANDATORY OUTPUT FORMAT
================================================================================

After analyzing all training pairs above, write ONE final
`def solve(input_grid):` that generalizes across all training pairs AND the
test input.

STATED_RULE: <one sentence describing the transformation rule your code implements>

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
- STATED_RULE must be a single sentence on its own line, starting with
  "STATED_RULE: ". It must describe the transformation the code performs —
  not the failure mode, not the bug fix, not the diff against a prior attempt.
- The python must generalize across all training pairs.
- The function must work on grids of any size (do not hardcode dimensions).
- Return a 2D list of integers (colors 0-9).
- TEST_OUTPUT must equal solve(test_input).
"""


def format_grid(grid: List[List[int]]) -> str:
    return "\n".join(str(row) for row in grid)


def _format_training_pairs(puzzle: Dict[str, Any], include_analysis: bool = True) -> str:
    parts = []
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
        if include_analysis:
            parts.append(PER_PAIR_ANALYSIS)
    return "\n".join(parts)


def _format_test_input(puzzle: Dict[str, Any]) -> str:
    if not puzzle.get("test"):
        return ""
    parts = [
        "=" * 80,
        "TEST INPUT",
        "=" * 80,
        "",
        format_grid(puzzle["test"][0]["input"]),
        "",
    ]
    return "\n".join(parts)


def generate_seed_prompt(puzzle: Dict[str, Any]) -> str:
    """Iter-1 seed prompt. Per-pair structured analysis + final solve()."""
    return "\n".join([
        TASK_STATEMENT,
        "",
        _format_training_pairs(puzzle),
        _format_test_input(puzzle),
        OUTPUT_FORMAT,
    ])


def build_iteration_prompt(puzzle: Dict[str, Any],
                           prior_code: str,
                           diagnosis_block: str,
                           iter_n: int) -> str:
    """Iter-N prompt for stateless API calls.

    iter_n is the NEW iter number being generated (so prior_code is iter_n-1's
    code). Self-contained: includes seed structure + prior code + diagnosis +
    update instruction. No chat history required.
    """
    parts = [
        TASK_STATEMENT,
        "",
        _format_training_pairs(puzzle, include_analysis=False),
        _format_test_input(puzzle),
        "=" * 80,
        f"YOUR PREVIOUS CODE (iter {iter_n - 1})",
        "=" * 80,
        "",
        "```python",
        prior_code.rstrip(),
        "```",
        "",
        diagnosis_block,
        "",
        "=" * 80,
        f"TASK FOR ITER {iter_n}",
        "=" * 80,
        "",
        "Update your `def solve(input_grid):` function based on the diagnosis "
        "above. Preserve the logic that produces the correct output for "
        "passing training pair(s); fix what's wrong with the failing one(s). "
        "Return the full updated function plus an updated TEST_OUTPUT.",
        "",
        OUTPUT_FORMAT,
    ]
    return "\n".join(parts)


FRESH_REFINE_TASK = (
    "Solve this ARC-AGI puzzle. A previous attempt got a partial result — its "
    "code, its stated rule, and per-pair outcomes are below. Your job is to "
    "deliver a `def solve(input_grid):` that passes ALL training pairs and "
    "generalizes to the test input."
)


FRESH_REFINE_JUDGE_BLOCK = """\
================================================================================
YOUR TASK — JUDGE THEN REPAIR
================================================================================

Phase 1 — Judge. Pick exactly one before writing any code:
  A. The stated rule is correct; the code has a small implementation bug.
  B. The stated rule is wrong or overfit; the abstraction must change.

Justify your choice in 1-2 sentences using the failing training pair(s). If \
a failing pair's correct output cannot be produced by ANY parameter tuning \
of the stated rule, you must pick B.

Phase 2 — Repair.
  - If A: produce a minimal patch that preserves the logic which passes the \
currently passing pair(s).
  - If B: write a new one-sentence rule, then write a new `def solve()` from \
scratch based on it.

Hard constraints (any violation invalidates the answer):
  - Do not hardcode grid dimensions, pair IDs, or specific mismatch cells.
  - Do not add special cases unless they follow from the task rule itself.
  - If the previous code added a special case that fixes some cells but \
would clearly break other regions of the grid, that is evidence for B, not \
a license to add another special case."""


def _format_training_pairs_with_status(puzzle: Dict[str, Any],
                                       pair_status: Dict[int, str]) -> str:
    parts = []
    for idx, pair in enumerate(puzzle["train"], 1):
        status = pair_status.get(idx, "?")
        parts.append("=" * 80)
        parts.append(f"TRAINING PAIR {idx}  [previous attempt: {status}]")
        parts.append("=" * 80)
        parts.append("")
        parts.append("INPUT:")
        parts.append(format_grid(pair["input"]))
        parts.append("")
        parts.append("OUTPUT:")
        parts.append(format_grid(pair["output"]))
        parts.append("")
    return "\n".join(parts)


def build_fresh_refine_prompt(puzzle: Dict[str, Any],
                              prior_code: str,
                              prior_rule: str,
                              pair_status: Dict[int, str],
                              rejected_rules: List[str] = None,
                              observations_block: str = "") -> str:
    """Fresh-refinement prompt: judge prior rule, then patch or replace.

    pair_status maps 1-indexed pair number to a status string like "PASS" or
    "FAIL (26/400 cells wrong)". Both the rule and the code come from the
    model's own prior output, so this prompt leaks no information that wasn't
    derivable from the puzzle file + the model's previous attempt.

    rejected_rules: optional list of one-sentence rules the model has already
    proposed and seen fail; included so a second fresh refinement on the same
    puzzle doesn't re-propose them.

    observations_block: optional pre-formatted OBSERVED PATTERN block from
    feedback_diagnostics.format_observations_block(). Rides along when a
    detector fingerprint matched or a structural diff was found. The block
    describes the spatial pattern of training-pair errors but does NOT
    prescribe a fix — that judgment is left to the model's Phase 1 step.
    Comp-clean: everything in the block is derived from training-pair errors.
    """
    parts = [
        FRESH_REFINE_TASK,
        "",
        _format_training_pairs_with_status(puzzle, pair_status),
        _format_test_input(puzzle),
        "=" * 80,
        "PREVIOUS ATTEMPT'S STATED RULE",
        "=" * 80,
        "",
        prior_rule.strip(),
        "",
    ]
    if rejected_rules:
        parts.extend([
            "=" * 80,
            "RULES ALREADY TRIED AND REJECTED ON THIS PUZZLE",
            "=" * 80,
            "",
        ])
        for r in rejected_rules:
            parts.append(f"- {r.strip()}")
        parts.append("")
    parts.extend([
        "=" * 80,
        "PREVIOUS CODE",
        "=" * 80,
        "",
        "```python",
        prior_code.rstrip(),
        "```",
        "",
    ])
    if observations_block:
        parts.append(observations_block.rstrip())
        parts.append("")
    parts.extend([
        FRESH_REFINE_JUDGE_BLOCK,
        "",
        OUTPUT_FORMAT,
    ])
    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("usage: python seed_prompt.py <puzzle.json> [out_path]",
              file=sys.stderr)
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
