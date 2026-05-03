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
    """
    Compute the background color as the majority color in the grid.
    
    Args:
        grid: 2D list of integers representing cell colors
        
    Returns:
        The most frequent color value (background)
    """
    flat = [cell for row in grid for cell in row]
    return Counter(flat).most_common(1)[0][0]


def compute_transition(input_val: int, output_val: int, background: int) -> str:
    """
    Determine the transition symbol for a single cell.
    
    Args:
        input_val: Color value in input grid
        output_val: Color value in output grid
        background: The background color (majority)
        
    Returns:
        Single-character transition symbol
    """
    if input_val == output_val:
        # No change
        if input_val == background:
            return '.'  # background unchanged
        else:
            return '='  # colored cell unchanged (anchor)
    elif input_val == background and output_val != background:
        return '+'  # background → color (activation)
    elif input_val != background and output_val == background:
        return '-'  # color → background (deactivation)
    else:
        # Both non-background but different values
        return '~'  # color → different color (recolor)


def generate_transformation_grid(input_grid: Grid, output_grid: Grid) -> Tuple[TransformationGrid, int]:
    """
    Generate transformation grid comparing input and output.
    
    Args:
        input_grid: The puzzle input grid
        output_grid: The puzzle output grid
        
    Returns:
        Tuple of (transformation_grid, background_color)
    """
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


def format_transformation_grid(trans_grid: TransformationGrid, 
                               title: str = None,
                               spacing: int = 2) -> str:
    """
    Format transformation grid as aligned text.
    
    Args:
        trans_grid: The transformation grid
        title: Optional title to print above grid
        spacing: Number of spaces between symbols (default: 2)
        
    Returns:
        Formatted string representation
    """
    lines = []
    
    if title:
        lines.append(f"\n{title}")
        lines.append("=" * 80)
    
    sep = " " * spacing
    for row in trans_grid:
        lines.append("  " + sep.join(row))
    
    return "\n".join(lines)


def print_transformation_grid(trans_grid: TransformationGrid,
                              title: str = None,
                              spacing: int = 2) -> None:
    """
    Print transformation grid to stdout.
    
    Args:
        trans_grid: The transformation grid
        title: Optional title to print above grid
        spacing: Number of spaces between symbols (default: 2)
    """
    print(format_transformation_grid(trans_grid, title, spacing))
    print()  # Extra newline


def get_transition_counts(trans_grid: TransformationGrid) -> dict:
    """
    Count occurrences of each transition type.
    
    Useful for understanding the transformation at a glance.
    
    Args:
        trans_grid: The transformation grid
        
    Returns:
        Dictionary mapping symbol → count
    """
    flat = [cell for row in trans_grid for cell in row]
    return Counter(flat)


def get_changed_cells(trans_grid: TransformationGrid) -> List[Tuple[int, int, str]]:
    """
    Extract all cells that changed (not '.' or '=').
    
    Args:
        trans_grid: The transformation grid
        
    Returns:
        List of (row, col, symbol) tuples for changed cells
    """
    changed = []
    for r, row in enumerate(trans_grid):
        for c, symbol in enumerate(row):
            if symbol not in ('.', '='):
                changed.append((r, c, symbol))
    return changed


# Example usage
if __name__ == "__main__":
    # Example: simple vertical beam extension
    input_grid = [
        [8, 8, 8],
        [8, 8, 8],
        [8, 1, 8],
        [8, 1, 8],
    ]
    
    output_grid = [
        [8, 2, 8],
        [8, 2, 8],
        [8, 1, 8],
        [8, 1, 8],
    ]
    
    # Generate transformation grid
    trans_grid, bg = generate_transformation_grid(input_grid, output_grid)
    
    # Print it
    print_transformation_grid(
        trans_grid,
        title=f"Example Transformation (background: {bg})"
    )
    
    # Get statistics
    counts = get_transition_counts(trans_grid)
    print(f"Transition counts: {counts}")
    
    # Get changed cells
    changed = get_changed_cells(trans_grid)
    print(f"Changed cells: {changed}")
