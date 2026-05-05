"""
Complete Substrate Feedback System
Combines transformation grids + diff maps + mechanistic analysis

Provides two modes:
  1. generate_complete_substrate_feedback() - full diff vs ground truth (training)
  2. generate_test_self_inspection()        - no ground truth, code self-view (test)
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
                row_str.append(f"X")
            else:
                row_str.append(f"{expected[r][c]}")
        diff_map.append("[" + ", ".join(f"{v:>2}" for v in row_str) + "]")
    
    return "\n".join(diff_map), errors


def generate_complete_substrate_feedback(
    input_grid: List[List[int]],
    expected_output: List[List[int]],
    actual_output: List[List[int]],
    pair_number=None
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
    
    rows = len(expected_output)
    cols = len(expected_output[0])
    error_count = sum(
        1 for r in range(rows) for c in range(cols)
        if expected_output[r][c] != actual_output[r][c]
    )
    
    if error_count == 0:
        feedback += "PERFECT! All cells match expected output.\n\n"
        return feedback
    
    feedback += f"ERRORS: {error_count} / {rows * cols} cells wrong\n\n"
    
    # 1. SIDE-BY-SIDE GRID COMPARISON
    feedback += "=" * 80 + "\n"
    feedback += "GRID COMPARISON\n"
    feedback += "=" * 80 + "\n\n"
    feedback += "EXPECTED OUTPUT:\n"
    for row in expected_output:
        feedback += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    feedback += "\nYOUR OUTPUT:\n"
    for row in actual_output:
        feedback += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    feedback += "\n"
    
    # 2. DIFF MAP
    feedback += "=" * 80 + "\n"
    feedback += "DIFF MAP (X = error)\n"
    feedback += "=" * 80 + "\n\n"
    diff_map, error_positions = generate_diff_map(expected_output, actual_output)
    feedback += diff_map + "\n\n"
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
    expected_trans, _ = generate_transformation_grid(input_grid, expected_output)
    feedback += "EXPECTED TRANSFORMATION:\n"
    for row in expected_trans:
        # Pad each symbol to 2 chars so columns visually align with data grids
        feedback += "[" + ", ".join(f"{s:>2}" for s in row) + "]\n"
    feedback += "\nYOUR TRANSFORMATION:\n"
    actual_trans, _ = generate_transformation_grid(input_grid, actual_output)
    for row in actual_trans:
        feedback += "[" + ", ".join(f"{s:>2}" for s in row) + "]\n"
    feedback += "\n"
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
    feedback += generate_mechanistic_feedback(input_grid, expected_output, actual_output)
    return feedback


def generate_test_self_inspection(test_input, solve_output) -> str:
    """
    Self-inspection view for the test case (no ground truth available).
    Shows: test input + solve(test_input) + transformation grid the code applied.
    No diff/mechanistic - just lets the LLM compare its own rule on the test
    against the rules it should have produced on training pairs.
    """
    out = "=" * 80 + "\n"
    out += "TEST SELF-INSPECTION (no ground truth)\n"
    out += "=" * 80 + "\n\n"
    out += (
        "This is what your code produced on the test input. "
        "Compare the transformation grid below against the (correct) "
        "transformation grids from your training pairs. "
        "If the rule you applied here looks different in shape or kind, "
        "your algorithm did not generalize.\n\n"
    )

    out += "TEST INPUT:\n"
    for row in test_input:
        out += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    out += "\n"

    out += "YOUR CODE'S TEST OUTPUT (what would be submitted):\n"
    for row in solve_output:
        out += "[" + ", ".join(f"{v:>2}" for v in row) + "]\n"
    out += "\n"

    trans, _ = generate_transformation_grid(test_input, solve_output)
    out += "TRANSFORMATION RULE YOUR CODE APPLIED:\n"
    out += "Symbols: . = unchanged, = = preserved, + = activated, - = removed\n\n"
    for row in trans:
        # Pad each symbol to 2 chars so columns visually align with data grids
        out += "[" + ", ".join(f"{s:>2}" for s in row) + "]\n"
    out += "\n"

    return out
