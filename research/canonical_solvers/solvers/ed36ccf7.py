"""Canonical solver for ARC puzzle ed36ccf7.

Rule: the grid is rotated 90 degrees counter-clockwise. Equivalently, the
cell at output position (r, c) takes the value of the input cell at
(c, W-1-r). infer_T derives this mapping as a latent mask of target cells to
new colors; apply_T overwrites those cells on a copy of the input.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Latent transformation mask: target cell -> new color under a 90deg CCW
    # rotation. Built purely from the input's geometry, no hardcoding.
    T = {}
    for r in range(H):
        for c in range(W):
            src_r = c
            src_c = W - 1 - r
            if 0 <= src_r < H and 0 <= src_c < W:
                T[(r, c)] = input_grid[src_r][src_c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H = len(out)
    W = len(out[0])
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
