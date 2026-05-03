"""
Complete Substrate Feedback System
Combines transformation grids + diff maps + mechanistic analysis
"""

import json
from typing import List, Dict, Any
from transformation_grid import generate_transformation_grid
from mechanistic_feedback_generator import generate_mechanistic_feedback


def format_grid_with_highlights(grid: List[List[int]], 
                                errors: set = None) -> str:
    """Format grid with error highlighting"""
    lines = []
    for r, row in enumerate(grid):
        formatted = []
        for c, val in enumerate(row):
            if errors and (r, c) in errors:
                formatted.append(f"X")  # Mark errors
            else:
                formatted.append(str(val))
        lines.append("[" + ", ".join(f"{v:>2}" for v in formatted) + "]")
    return "\n".join(lines)


def generate_diff_map(expected: List[List[int]], 
                     actual: List[List[int]]) -> str:
    """Generate visual diff map showing errors"""
    rows = len(expected)
    cols = len(expected[0])
    
    errors = set()
    for r in range(rows):
        for c in range(cols):
            if expected[r][c] != actual[r][c]:
                errors.add((r, c))
    
    diff_map = []
    for r in range(rows):
        row_str = []
        for c in range(cols):
            if (r, c) in errors:
                exp = expected[r][c]
                act = actual[r][c]
                row_str.append(f"X")  # Mark error position
            else:
                row_str.append(f"{expected[r][c]}")
        diff_map.append("[" + ", ".join(f"{v:>2}" for v in row_str) + "]")
    
    return "\n".join(diff_map), errors


def generate_complete_substrate_feedback(
    input_grid: List[List[int]],
    expected_output: List[List[int]],
    actual_output: List[List[int]],
    pair_number: int = None
) -> str:
    """
    Generate complete substrate feedback with:
    1. Grid comparisons (expected vs actual)
    2. Diff map (visual error highlighting)
    3. Transformation grids (substrate encoding)
    4. Mechanistic analysis
    """
    
    feedback = "=" * 80 + "\n"
    if pair_number:
        feedback += f"SUBSTRATE FEEDBACK - PAIR {pair_number}\n"
    else:
        feedback += "SUBSTRATE FEEDBACK\n"
    feedback += "=" * 80 + "\n\n"
    
    # Count errors
    rows = len(expected_output)
    cols = len(expected_output[0])
    error_count = sum(
        1 for r in range(rows) for c in range(cols)
        if expected_output[r][c] != actual_output[r][c]
    )
    
    if error_count == 0:
        feedback += "✓✓✓ PERFECT! All cells match expected output.\n\n"
        return feedback
    
    feedback += f"ERRORS: {error_count} / {rows * cols} cells wrong\n\n"
    
    # 1. SIDE-BY-SIDE GRID COMPARISON
    feedback += "=" * 80 + "\n"
    feedback += "GRID COMPARISON\n"
    feedback += "=" * 80 + "\n\n"
    
    feedback += "EXPECTED OUTPUT:\n"
    for row in expected_output:
        feedback += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    feedback += "\n"
    
    feedback += "YOUR OUTPUT:\n"
    for row in actual_output:
        feedback += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    feedback += "\n"
    
    # 2. DIFF MAP (Visual error highlighting)
    feedback += "=" * 80 + "\n"
    feedback += "DIFF MAP (X = error)\n"
    feedback += "=" * 80 + "\n\n"
    
    diff_map, error_positions = generate_diff_map(expected_output, actual_output)
    feedback += diff_map + "\n\n"
    
    # Show specific errors
    feedback += "ERROR DETAILS (first 10):\n"
    for i, (r, c) in enumerate(sorted(error_positions)[:10]):
        exp = expected_output[r][c]
        act = actual_output[r][c]
        inp = input_grid[r][c]
        feedback += f"  ({r:2}, {c:2}): input={inp}, expected={exp}, got={act}\n"
    
    if len(error_positions) > 10:
        feedback += f"  ... and {len(error_positions) - 10} more errors\n"
    feedback += "\n"
    
    # 3. TRANSFORMATION GRIDS
    feedback += "=" * 80 + "\n"
    feedback += "TRANSFORMATION GRID ANALYSIS\n"
    feedback += "=" * 80 + "\n\n"
    
    feedback += "Symbols: . = unchanged, = = preserved, + = activated, - = removed\n\n"
    
    # Expected transformation
    expected_trans, _ = generate_transformation_grid(input_grid, expected_output)
    feedback += "EXPECTED TRANSFORMATION:\n"
    for row in expected_trans:
        feedback += "[" + ", ".join(row) + "]\n"
    feedback += "\n"
    
    # Actual transformation
    actual_trans, _ = generate_transformation_grid(input_grid, actual_output)
    feedback += "YOUR TRANSFORMATION:\n"
    for row in actual_trans:
        feedback += "[" + ", ".join(row) + "]\n"
    feedback += "\n"
    
    # Transformation diff
    trans_errors = 0
    feedback += "TRANSFORMATION MISMATCHES:\n"
    for r in range(len(expected_trans)):
        for c in range(len(expected_trans[0])):
            if expected_trans[r][c] != actual_trans[r][c]:
                trans_errors += 1
                if trans_errors <= 10:
                    feedback += f"  ({r:2}, {c:2}): expected '{expected_trans[r][c]}', got '{actual_trans[r][c]}'\n"
    
    if trans_errors > 10:
        feedback += f"  ... and {trans_errors - 10} more mismatches\n"
    feedback += "\n"
    
    # 4. MECHANISTIC ANALYSIS
    feedback += "=" * 80 + "\n"
    feedback += "MECHANISTIC ANALYSIS\n"
    feedback += "=" * 80 + "\n\n"
    
    mechanistic = generate_mechanistic_feedback(input_grid, expected_output, actual_output)
    feedback += mechanistic
    
    return feedback


# CLI interface
if __name__ == "__main__":
    import sys
    
    # Test on Gemini Pair 1
    with open('puzzle_28a6681f.json', 'r') as f:
        puzzle = json.load(f)
    
    from gemini_solver_v10 import solve
    
    pair = puzzle['train'][0]
    actual = solve(pair['input'])
    
    feedback = generate_complete_substrate_feedback(
        pair['input'],
        pair['output'],
        actual,
        pair_number=1
    )
    
    print(feedback)
    
    # Save to file
    with open('/mnt/user-data/outputs/COMPLETE_SUBSTRATE_FEEDBACK_DEMO.txt', 'w') as f:
        f.write(feedback)
    
    print("\n✓ Saved to /mnt/user-data/outputs/COMPLETE_SUBSTRATE_FEEDBACK_DEMO.txt")
