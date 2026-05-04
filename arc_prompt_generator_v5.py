"""
ARC-AGI Prompt Generator with Transformation Rules
v6: Strengthen output-format requirements
    - mandatory `def solve(input_grid):` function (no hand-computed grids)
    - explicit "do not hardcode dimensions/indices" — must work on any size
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
MANDATORY OUTPUT FORMAT — read this first
================================================================================

Your response MUST contain a Python function `solve(input_grid)` that returns
the test output grid. We run your code on every training pair AND the test
input, then validate by comparing actual outputs to expected outputs.

DO NOT hand-compute the test output grid yourself. DO NOT output a grid as
your final answer. Only the code is evaluated.

If your response contains no `def solve(input_grid):` function, the iteration
is invalid and we cannot give you any feedback.

================================================================================
TRANSFORMATION ENCODING
================================================================================

I have examples showing pairs of training inputs, outputs, and transformation rule.
The transformation rule symbols are atomic operations applied cell-by-cell:
+ activates, = preserves, - deactivates, . maintains background.
The transformation rule IS the pattern (not a description of it).

Transformation rule symbols:
  . = background unchanged
  = = structural element (stays)
  + = background activated (drawn border)
  - = color deactivated (removed)

Your task: study the transformation rule across all training examples,
write Python that applies the same rule to any input grid.

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
    prompt += "YOUR TASK\n"
    prompt += "=" * 80 + "\n\n"
    prompt += """
Write a Python function that applies the same transformation rule from the
training examples to ANY input grid. Your code will be run on all 3 training
inputs and on the test input — it must produce the correct output for each.

```python
def solve(input_grid):
    # input_grid: 2D list of integers (colors 0-9)
    # return:     2D list of integers (output grid)

    # YOUR ALGORITHM HERE

    return output_grid
```

REQUIREMENTS
- Output ONLY the function (you may include reasoning before it, but the
  function is what gets executed).
- The function must work on grids of varying sizes — do not hardcode
  dimensions, row indices, or column indices.
- Return a 2D list of integers (colors 0-9).

DO NOT manually write out the test output grid. We will compute it by running
your code. If you do not include a `def solve(input_grid):` function, we
cannot validate your iteration and you will receive no feedback.
"""
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
    print("PROMPT GENERATOR v6 - CODE MANDATORY, NO HARDCODED GRIDS")
    print("=" * 80)
    print(f"\nTraining examples: {len(puzzle['train'])}")
    print(f"Prompt size: {size:,} characters")
    print(f"Saved to: {output_file}")
