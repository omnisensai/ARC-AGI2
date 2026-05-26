"""Canonical solver for ARC puzzle ce9e57f2.

Rule: the grid contains vertical bars (contiguous runs) of color 2. For each
bar, the bottom floor(height/2) cells are recolored to 8; the rest stay 2.
"""

FILL = 8
BAR = 2


def infer_T(input_grid):
    """Infer the latent transformation mask {(r, c): new_color}.

    Find each maximal contiguous vertical run of BAR-colored cells in every
    column and mark its bottom floor(height/2) cells to become FILL.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    T = {}
    for c in range(W):
        r = 0
        while r < H:
            if input_grid[r][c] == BAR:
                start = r
                while r < H and input_grid[r][c] == BAR:
                    r += 1
                end = r  # exclusive
                height = end - start
                n_fill = height // 2
                # bottom n_fill cells of the run
                for rr in range(end - n_fill, end):
                    T[(rr, c)] = FILL
            else:
                r += 1
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
