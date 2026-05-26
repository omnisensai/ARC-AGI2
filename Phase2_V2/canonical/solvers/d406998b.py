"""Canonical solver for ARC puzzle d406998b.

Structure of every pair: a 3-row grid whose only non-zero cells are 5s, with
exactly one 5 in each column (a zig-zag path across the columns). The output
recolors the 5 to 3 in every other column. The selected columns are anchored at
the rightmost column and step leftward two at a time: column c is selected iff
(W-1 - c) is even. Cells outside the selected columns (and the background) are
left untouched.
"""


def _columns_with_marker(grid, marker):
    """Return the list of column indices that contain at least one `marker`."""
    H = len(grid)
    W = len(grid[0]) if H else 0
    cols = []
    for c in range(W):
        if any(grid[r][c] == marker for r in range(H)):
            cols.append(c)
    return cols


def infer_T(input_grid):
    """Infer a latent transformation mask {(r, c): new_color}.

    The mask marks, for every other column (counted from the right edge), the
    single 5-cell in that column to be recolored to 3.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    marker = 5
    new_color = 3

    T = {}
    cols = _columns_with_marker(input_grid, marker)
    for c in cols:
        # Anchor the alternating selection at the rightmost column.
        if (W - 1 - c) % 2 != 0:
            continue
        for r in range(H):
            if input_grid[r][c] == marker:
                T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    """Copy the input grid and overwrite only the cells named in the mask."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
