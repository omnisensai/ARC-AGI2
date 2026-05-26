def infer_T(input_grid):
    """Latent mask: for every horizontal pattern 1,0,1, the middle 0 becomes 2."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W - 2):
            if (input_grid[r][c] == 1 and
                    input_grid[r][c + 1] == 0 and
                    input_grid[r][c + 2] == 1):
                T[(r, c + 1)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
