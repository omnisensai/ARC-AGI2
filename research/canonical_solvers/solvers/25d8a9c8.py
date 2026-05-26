def infer_T(input_grid):
    """Latent mask: each cell gets 5 if its row is uniform (all same color),
    else 0. Computed from input row structure alone."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        row = input_grid[r]
        uniform = all(v == row[0] for v in row)
        fill = 5 if uniform else 0
        for c in range(W):
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
