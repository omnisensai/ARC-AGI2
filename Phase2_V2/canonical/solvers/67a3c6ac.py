def infer_T(input_grid):
    # Rule: mirror the grid horizontally (reverse each row).
    # T is a latent mask mapping every cell to the color of its
    # left-right mirror partner in the same row.
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            mirror = input_grid[r][W - 1 - c]
            if mirror != input_grid[r][c]:
                T[r][c] = mirror
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
