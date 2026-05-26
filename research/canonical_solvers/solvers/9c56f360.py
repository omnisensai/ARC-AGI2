"""Canonical solver for ARC puzzle 9c56f360.

Rule: each horizontal run of color-3 cells in a row is a rigid object that
slides left across background (0) cells until its leading edge is blocked by
an 8 (or the grid's left border), stopping just to the right of the obstacle.
The original 3 cells revert to background; the run reappears at its new spot.
infer_T builds the latent mask {(r,c): 3} of the destination cells; apply_T
clears the old 3s and stamps the mask onto a copy of the input.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        c = 0
        while c < W:
            if input_grid[r][c] == 3:
                c0 = c
                while c < W and input_grid[r][c] == 3:
                    c += 1
                width = c - c0
                # slide the run left over background (0) cells
                left = c0
                while left - 1 >= 0 and input_grid[r][left - 1] == 0:
                    left -= 1
                for k in range(width):
                    T[(r, left + k)] = 3
            else:
                c += 1
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if out[r][c] == 3:
                out[r][c] = 0
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
