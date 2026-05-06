"""
ARC Transformation Grid Generator

Computes minimal binary transition encoding for ARC puzzle transformations.
Each cell has at most one state change: background ↔ color, or color → color.

Encoding:
    .  = background unchanged
    =  = colored cell unchanged (structural anchor)
    +  = background → color (activation)
    -  = color → background (deactivation)
    ~  = color → different color (recolor)
"""

from collections import Counter
from typing import List, Tuple

Grid = List[List[int]]
TransformationGrid = List[List[str]]


def get_background_color(grid: Grid) -> int:
    flat = [cell for row in grid for cell in row]
    return Counter(flat).most_common(1)[0][0]


def compute_transition(input_val: int, output_val: int, background: int) -> str:
    if input_val == output_val:
        if input_val == background:
            return '.'
        else:
            return '='
    elif input_val == background and output_val != background:
        return '+'
    elif input_val != background and output_val == background:
        return '-'
    else:
        return '~'


def generate_transformation_grid(input_grid: Grid, output_grid: Grid) -> Tuple[TransformationGrid, int]:
    background = get_background_color(input_grid)
    rows = len(input_grid)
    cols = len(input_grid[0])
    trans_grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            symbol = compute_transition(
                input_grid[r][c],
                output_grid[r][c],
                background
            )
            row.append(symbol)
        trans_grid.append(row)
    return trans_grid, background
