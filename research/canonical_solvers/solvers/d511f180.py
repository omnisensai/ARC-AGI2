def infer_T(input_grid):
    """Infer a latent transformation mask.

    The transformation is a color involution: the two distinguished colors
    5 (gray) and 8 (azure) are mutually exchanged everywhere they occur,
    while all other cells stay fixed.  The mask marks exactly those cells
    holding one of the two swapped colors and records its swapped value.
    """
    H, W = len(input_grid), len(input_grid[0])
    SWAP = {5: 8, 8: 5}

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in SWAP:
                T[(r, c)] = SWAP[v]
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
