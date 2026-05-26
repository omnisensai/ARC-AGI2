def infer_T(input_grid):
    """Latent mask: for every 8-cell decide its recolor.

    The grid has a top/bottom (horizontal-axis) reflection structure. An 8 cell
    is recolored 2 when its vertical mirror (same column, row H-1-r) is also an
    8 (i.e. it is symmetric under the flip), otherwise it is recolored 5. Cells
    that are 0 are left untouched (not in the mask).
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 8:
                mirror_is_8 = (input_grid[H - 1 - r][c] == 8)
                T[(r, c)] = 2 if mirror_is_8 else 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
