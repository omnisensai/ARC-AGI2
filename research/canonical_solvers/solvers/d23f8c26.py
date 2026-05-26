"""Canonical ARC solver for puzzle d23f8c26.

Rule: the grid is reduced to its central vertical axis. Every cell that is not
on the center column (index W//2) is cleared to background 0, while the center
column keeps its original values. This is expressed as a latent mask of the
cells to overwrite (everything off the central column).
"""


def infer_T(input_grid):
    """Infer the transformation mask.

    The mask marks every cell NOT on the central column for overwrite to 0.
    The center column is determined purely from the grid width.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    center = W // 2
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if c != center:
                T[r][c] = 0
    return T


def apply_T(input_grid, T):
    """Copy input and overwrite only masked cells."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
