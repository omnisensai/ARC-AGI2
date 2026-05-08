"""
ARC-AGI Prompt Generator with Transformation Rules
v6: TIPS moved to right before TEST INPUT (recency anchor at code-generation moment)
"""
# Substrate prompt template version: V1

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
TIPS - read before writing code
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
cluster equally - do not redefine it per cell.

GLOBAL STRUCTURE BEFORE LOCAL CELLS
Before analyzing cells one by one, zoom out and look at the whole grid as
an image. Some rules are not about individual cells at all - they are
about whole regions wanting to be a repeating motif.

Blur-your-eyes test: if a region shows a regular repeating pattern,
the rule is probably 'complete / restore the motif,' not 'transform each
cell by a local rule.' Cells that break the pattern are corruptions to fix.

"""


def generate_prompt(puzzle: Dict[str, Any], include_test: bool = True) -> str:
    prompt = """You are an ARC-AGI solver.

Your task: extract the given transformation rule and write a Python
`def solve(input_grid):` function that applies the same rule to ALL input
grids and produces the same output grids.

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
  ~ = color recolored (one color -> different color)

The transformation rule IS the pattern. The same rule applies to every
training pair AND to the test input.

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
        "Return BOTH a `def solve(input_grid):` function AND a hand-written\n"
        "test output grid.\n\n"
        "Format your response with both blocks:\n\n"
        "```python\n"
        "def solve(input_grid):\n"
        "    return output_grid\n"
        "```\n\n"
        "TEST_OUTPUT = [\n"
        "    [...row 0 values...],\n"
        "    ...\n"
        "]\n\n"
        "REQUIREMENTS\n"
        "- BOTH the def solve function AND the TEST_OUTPUT block are required.\n"
        "- The function must work on grids of varying sizes.\n"
        "- Return 2D lists of integers (colors 0-9).\n"
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
