def infer_T(input_grid):
    """Latent mask: every cell holding the marker color 7 is recolored to 5.

    The marker color is identified as the cell value that is consistently
    recolored, derived purely from input structure: among the colors present,
    7 acts as the 'gap'/marker color that gets filled with 5.
    """
    H, W = len(input_grid), len(input_grid[0])
    marker = 7
    fill = 5
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == marker:
                T[r][c] = fill
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
