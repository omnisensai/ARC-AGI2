def infer_T(input_grid):
    """Infer a latent mask: each 0 cell takes the color of the nearest
    non-zero cell above it in the same column (downward propagation)."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for c in range(W):
        last = None
        for r in range(H):
            v = input_grid[r][c]
            if v != 0:
                last = v
            elif last is not None:
                T[r][c] = last
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
