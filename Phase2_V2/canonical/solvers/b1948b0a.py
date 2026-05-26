def infer_T(input_grid):
    """Latent mask: every cell holding color 6 is recolored to 2.

    The transformation recolors the foreground color (6) to (2) while
    leaving the background color (7) untouched. The mask marks exactly
    those cells whose value is 6.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 6:
                T[r][c] = 2
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
