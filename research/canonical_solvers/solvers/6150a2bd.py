def infer_T(input_grid):
    """Latent transformation mask: 180-degree rotation.
    Each cell (r,c) gets the color from the diagonally-opposite cell
    (H-1-r, W-1-c). Computed from the input grid alone."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W):
            T[(r, c)] = input_grid[H - 1 - r][W - 1 - c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
