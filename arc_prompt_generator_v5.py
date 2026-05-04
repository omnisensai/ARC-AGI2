"""
ARC-AGI Prompt Generator with Transformation Rules
v10: Added cluster-property propagation hint (cell-level reasoning is atomic,
     but cluster-level properties like edge-touching are component-wide facts)
"""

import json
from typing import List, Dict, Any
from transformation_grid import generate_transformation_grid


def format_grid(grid: List[List[int]], indent: int = 0) -> str:
    """Format a grid as a Python list"""
    spaces = " " * indent
    lines = []
    for row in grid:
        lines.append(f"{spaces}{row}")
    return "\n".join(lines)


def generate_transformation_section(input_grid: List[List[int]],
                                    output_grid: List[List[int]]) -> str:
    """Generate transformation grid using substrate symbols"""
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
- When checking adjacency, consider whether the rule includes diagonals
  (8-connectivity) or only cardinal neighbors (4-connectivity).
- A property describing a connected component (e.g. "this cluster is
  edge-touching" or "this cluster is reachable from the seed") applies to all
  cells of the cluster equally. Compute it once at cluster-classification
  time; don't re-derive it per cell.

Avoid magic-number thresholds (>=80%, size > N, exactly K clusters).
Prefer rules expressed in terms of topology (reachability, adjacency,
connectivity) anchored at a recognizable element.

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


def save_prompt(puzzle: Dict[str, Any], output_path: str):
    """Generate and save prompt to file"""
    prompt = generate_prompt(puzzle)
    with open(output_path, 'w') as f:
        f.write(prompt)
    return len(prompt)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python arc_prompt_generator_v5.py <puzzle.json> [output.txt]")
        sys.exit(1)

    puzzle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "arc_prompt.txt"

    with open(puzzle_file, 'r') as f:
        puzzle = json.load(f)

    size = save_prompt(puzzle, output_file)

    print("=" * 80)
    print("PROMPT GENERATOR v10 - TIPS now includes cluster-property propagation")
    print("=" * 80)
    print(f"\nTraining examples: {len(puzzle['train'])}")
    print(f"Prompt size: {size:,} characters")
    print(f"Saved to: {output_file}")
