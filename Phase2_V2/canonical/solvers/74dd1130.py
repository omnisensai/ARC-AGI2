def infer_T(input_grid):
    """Latent mask: reflect the grid across its main diagonal (transpose).

    For each output cell (r,c) the new color is input_grid[c][r]. The mask is
    a full None/int grid derived solely from the input's structure.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            T[r][c] = input_grid[c][r]
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
