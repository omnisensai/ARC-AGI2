"""Canonical solver for ARC puzzle ce039d91.

Rule: the grid holds 5-colored cells on a 0 background. Considering the global
left-right mirror axis of the grid, any 5 whose horizontally mirrored partner
(r, W-1-c) is also a 5 belongs to the left-right-symmetric structure and is
recolored to 1. A 5 with no mirror partner (an asymmetric stray) keeps color 5.

infer_T scans the input and builds an explicit mask of cells to recolor;
apply_T copies the input and overwrites only the masked cells.
"""


def infer_T(input_grid):
    """Return a latent transformation mask {(r, c): new_color}."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    fg = 5          # foreground color
    new_color = 1   # recolor for the symmetric structure

    fives = {(r, c)
             for r in range(H)
             for c in range(W)
             if input_grid[r][c] == fg}

    T = {}
    for (r, c) in fives:
        mirror = (r, W - 1 - c)
        if mirror in fives:
            T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the mask T."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
