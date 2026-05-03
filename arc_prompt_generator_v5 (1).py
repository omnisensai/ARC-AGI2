"""
ARC-AGI Prompt Generator with Transformation Rules
v5: Fixed symbol formatting (no confusing dashes)
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
    """
    Generate complete ARC-AGI prompt with transformation rules
    
    Args:
        puzzle: ARC puzzle dict with 'train' and 'test' keys
        include_test: Whether to include test case (True) or just training (False)
    
    Returns:
        Formatted prompt string
    """
    
    prompt = """You are an ARC-AGI solver.

I have examples showing pairs of training inputs, outputs, and transformation rule. 
The transformation rule symbols are atomic operations applied cell-by-cell: 
+ activates, = preserves, - deactivates, . maintains background. The transformation rule IS the pattern (not a description of it).

Your task: Study the transformation rule across examples, 
then apply the rule on the TEST INPUT to produce the TEST OUTPUT GRID.

Transformation rule symbols:
  . = background unchanged
  = = structural element (stays)  
  + = background activated (drawn border)
  - = color deactivated (removed)

"""
    
    # Add training examples
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
    
    # Add test case if requested
    if include_test and 'test' in puzzle and len(puzzle['test']) > 0:
        prompt += "=" * 80 + "\n"
        prompt += "TEST CASE\n"
        prompt += "=" * 80 + "\n\n"
        
        prompt += "TEST INPUT:\n"
        prompt += format_grid(puzzle['test'][0]['input']) + "\n\n"
    
    # Add instructions
    prompt += "=" * 80 + "\n"
    prompt += "YOUR TASK\n"
    prompt += "=" * 80 + "\n\n"
    
    prompt += """
Write Python that produces the TEST OUTPUT GRID.

def solve(input_grid):
    # input_grid: 2D list of integers (colors 0-9)
    # MUST return: 2D list of INTEGERS (actual colored output grid)
    
    # Study the transformation rule
    # Apply rule on test input and generate output
    
    # YOUR CODE HERE
    
    return output_grid  # [[int, int, ...], ...]

CRITICAL: Return actual COLORED GRID with integers 0-9!

The transformation rule shows the pattern. Your output must be actual colors.
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
    print("PROMPT GENERATOR v5 - CLEAN FORMATTING!")
    print("=" * 80)
    print(f"\n✓ Training examples: {len(puzzle['train'])}")
    print(f"✓ Prompt size: {size:,} characters")
    print(f"✓ Saved to: {output_file}")
    print("\n✓ No confusing dashes in symbol list")
