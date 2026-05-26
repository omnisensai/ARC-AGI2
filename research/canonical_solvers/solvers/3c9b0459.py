def infer_T(input_grid):
    """Latent mask: rotate the grid 180 degrees; mark cells whose value changes."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            nv = input_grid[H - 1 - r][W - 1 - c]
            if nv != input_grid[r][c]:
                T[r][c] = nv
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
