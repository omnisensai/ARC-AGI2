"""
ARC-AGI Prompt Generator with Transformation Rules
v6: TIPS moved to right before TEST INPUT (recency anchor at code-generation moment)

Difference from v5:
- v5 had TIPS at the top, after the encoding key, before training examples.
  TIPS was hundreds of tokens before the model needed to apply them.
- v6 places TIPS right before TEST INPUT, anchoring it at the moment the
  model has to write code (rather than at the moment it reads substrate).
- All training examples retain uniform structure (no fragmentation).
- Encoding key stays at top because the model needs symbol grammar BEFORE
  reading the first substrate grid.
- Task framing changed: rule is GIVEN (in substrate), not discovered. Model's
  job is to encode the given rule in Python.
"""

import json
from typing import List, Dict, Any
from transformation_grid import generate_transformation_grid


def format_grid(grid: List[List[int]], indent: int = 0) -> str:
    spaces = " " * indent
    lines = []
    for row in grid:
        lines.append(f"{spaces}{row}")
    return "\n".join(lines)


def generate_transformation_section(input_grid: List[List[int]],
                                    output_grid: List[List[int]]) -> str:
    result = generate_transformation_grid(input_grid, output_grid)
    trans_grid = result[0]
    lines = []
    for row in trans_grid:
        formatted_row = "[" + ", ".join(row) + "],"
        lines.append(formatted_row)
    return "\n".join(lines)


TIPS_BLOCK = """\
================================================================================
TIPS — read before writing code
================================================================================

Before writing code, scan the inputs:
- Look for anchor cells (unique colors, single markers, distinctive objects).
- Look for barriers (walls, lines, obstacles).
- Many ARC rules radiate outward from an anchor (BFS, flood-fill) rather than
  apply per-cell logic.
- When checking adjacency, decide 4-connectivity vs 8-connectivity per rule.

Avoid magic-number thresholds (>=80%, size > N, exactly K clusters).
Prefer rules expressed in terms of topology (reachability, adjacency,
connectivity) anchored at a recognizable element.

CLUSTER-LEVEL vs CELL-LEVEL PROPERTIES
A property describing a connected component applies to ALL cells of that
cluster equally — do not redefine it per cell.

Worked example: a vertical wall of 1s spanning rows 0..15 at column 6 is a
single cluster. It "touches the grid edge" because (0,6) and (15,6) lie on
the boundary. Therefore EVERY cell of that cluster — including (5,6), (8,6),
deep in the interior of the grid — inherits the "edge-touching" property.

Wrong: `if r == 0 or c == 0 or r == H-1 or c == W-1` (per-cell test).
Right: classify the cluster once, then propagate the result to every cell.

"""


def generate_prompt(puzzle: Dict[str, Any], include_test: bool = True) -> str:
    prompt = """You are an ARC-AGI solver.

Your task: extract the given transformation rule and write a Python
`def solve(input_grid):` function that applies the same rule to ALL input
grids and produces the same output grids. Your code must generalize across
all inputs and outputs.

================================================================================
TRANSFORMATION RULE ENCODING
================================================================================

Each training pair below includes input, output, and the transformation
rule that produced the output from the input. The rule is given as a grid
of atomic symbols applied cell-by-cell:

  . = background unchanged
  = = structural element (stays)
  + = background activated (drawn border / halo)
  - = color deactivated (removed)
  ~ = color recolored (one color → different color)

The transformation rule IS the pattern (not a description of it). The same
rule applies to every training pair AND to the test input — your job is to
encode that rule in Python so it produces the correct output for any input.

"""
    for idx, example in enumerate(puzzle['train'], 1):
        prompt += "=" * 80 + "\n"
        prompt += f"TRAINING EXAMPLE {idx}\n"
        prompt += "=" * 80 + "\n\n"
        prompt += "INPUT:\n"
        prompt += format_grid(example['input']) + "\n\n"
        prompt += "OUTPUT:\n"
        prompt += format_grid(example['output']) + "\n\n"
        prompt += "TRANSFORMATION RULE:\n"
        trans = generate_transformation_section(example['input'], example['output'])
        prompt += trans + "\n\n"

    # TIPS placed RIGHT BEFORE TEST INPUT — anchors at code-generation moment
    prompt += TIPS_BLOCK

    if include_test and 'test' in puzzle and len(puzzle['test']) > 0:
        prompt += "=" * 80 + "\n"
        prompt += "TEST INPUT\n"
        prompt += "=" * 80 + "\n\n"
        prompt += format_grid(puzzle['test'][0]['input']) + "\n\n"

    prompt += "=" * 80 + "\n"
    prompt += "MANDATORY OUTPUT FORMAT\n"
    prompt += "=" * 80 + "\n\n"
    prompt += (
        "Return a `def solve(input_grid):` function that works on grids of any "
        "size — we run your code on every training input and the test input.\n\n"
        "```python\n"
        "def solve(input_grid):\n"
        "    # input_grid: 2D list of integers (colors 0-9)\n"
        "    # return:     2D list of integers (output grid)\n\n"
        "    # YOUR ALGORITHM HERE\n\n"
        "    return output_grid\n"
        "```\n\n"
        "REQUIREMENTS\n"
        "- Output ONLY the function (you may include reasoning before it, but the\n"
        "  function is what gets executed).\n"
        "- The function must work on grids of varying sizes — do not hardcode\n"
        "  dimensions, row indices, or column indices.\n"
        "- Return a 2D list of integers (colors 0-9).\n\n"
        "DO NOT manually write out the test output grid. We will compute it by\n"
        "running your code. If your response does not contain a `def solve(input_grid):`\n"
        "function, we cannot validate your iteration and you will receive no feedback.\n"
    )
    return prompt


if __name__ == "__main__":
    import sys
    puzzle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "substrate_prompt_v6.txt"
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    prompt = generate_prompt(puzzle)
    with open(output_file, 'w') as f:
        f.write(prompt)
    print(f"OK Wrote {len(prompt):,} chars to {output_file}")
    print(f"   Training examples: {len(puzzle['train'])}")
