"""Canonical solver for ARC task e45ef808.

Structure: row 0 is a constant marker row (all 0). Below it, color-1 fills the
top region and color-6 forms "mountains" rising from the bottom, one peak height
per column. The transformation finds the tallest mountain (column whose topmost
6 sits highest = smallest row index) and the lowest mountain (topmost 6 lowest =
largest row index). It draws a vertical line of color 4 through the tallest
column and color 9 through the lowest column, filling the 1-cells from row 1 down
to just above that column's first 6.
"""


def _columns_top6(grid):
    H, W = len(grid), len(grid[0])
    tops = []
    for c in range(W):
        t = None
        for r in range(H):
            if grid[r][c] == 6:
                t = r
                break
        tops.append(t)
    return tops


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    tops = _columns_top6(input_grid)

    # Only consider columns that actually have a 6-mountain.
    cols = [c for c in range(W) if tops[c] is not None]
    if not cols:
        return {}

    # Tallest mountain = highest peak = smallest top row index -> color 4.
    # Lowest mountain  = lowest  peak = largest  top row index -> color 9.
    col_high = min(cols, key=lambda c: tops[c])   # tallest -> 4
    col_low = max(cols, key=lambda c: tops[c])    # lowest  -> 9

    T = {}

    def draw(col, color):
        # Fill from row 1 (below the marker row 0) up to just above the first 6.
        first6 = tops[col]
        for r in range(1, first6):
            if input_grid[r][col] != 6:
                T[(r, col)] = color

    draw(col_high, 4)
    draw(col_low, 9)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
