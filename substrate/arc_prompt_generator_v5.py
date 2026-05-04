"""
ARC-AGI Prompt Generator with Transformation Rules
v8: TIPS section + minimal one-line mandatory format reminder at bottom
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


def generate_prompt(puzzle: Dict[str, Any], include_test: bool = True) -> str:
    prompt = """You are an ARC-AGI solver.

================================================================================
TRANSFORMATION ENCODING
================================================================================

Each training pair below includes inputs, outputs, and a transformation rule
grid. The transformation rule symbols are atomic operations applied cell-by-cell:

  . = background unchanged
  = = structural element (stays)
  + = background activated (drawn border)
  - = color deactivated (removed)

The transformation rule IS the pattern (not a description of it). Study it
across all training examples, then encode the same rule in Python.

================================================================================
TIPS
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

    if include_test and 'test' in puzzle and len(puzzle['test']) > 0:
        prompt += "=" * 80 + "\n"
        prompt += "TEST CASE\n"
        prompt += "=" * 80 + "\n\n"
        prompt += "TEST INPUT:\n"
        prompt += format_grid(puzzle['test'][0]['input']) + "\n\n"

    prompt += "=" * 80 + "\n"
    prompt += "MANDATORY OUTPUT FORMAT\n"
    prompt += "=" * 80 + "\n\n"
    prompt += (
        "Return a `def solve(input_grid):` function that works on grids of any "
        "size — we run your code on every training input and the test input.\n"
    )
    return prompt


if __name__ == "__main__":
    import sys
    puzzle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "substrate_prompt.txt"
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    prompt = generate_prompt(puzzle)
    with open(output_file, 'w') as f:
        f.write(prompt)
    print(f"OK Wrote {len(prompt):,} chars to {output_file}")
    print(f"   Training examples: {len(puzzle['train'])}")
