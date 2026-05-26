def infer_T(input_grid):
    # Latent mask: for each cell, the new color is the cell from the
    # vertically-mirrored grid (rows reversed top-to-bottom).
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            src = input_grid[H - 1 - r][c]
            if src != input_grid[r][c]:
                T[r][c] = src
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
