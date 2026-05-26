def infer_T(input_grid):
    # Latent mask: the number of distinct colors in the input selects which
    # cells become 5 (the rest become 0). 1 color -> top row, 2 colors ->
    # main diagonal, 3 colors -> anti-diagonal.
    H, W = len(input_grid), len(input_grid[0])
    colors = set()
    for row in input_grid:
        for v in row:
            colors.add(v)
    n = len(colors)
    T = [[0] * W for _ in range(H)]  # default overwrite color is 0
    if n == 1:
        for c in range(W):
            T[0][c] = 5
    elif n == 2:
        for i in range(min(H, W)):
            T[i][i] = 5
    else:
        for i in range(min(H, W)):
            T[i][W - 1 - i] = 5
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
