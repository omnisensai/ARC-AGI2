def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # locate marker cells (color 1) on the main diagonal
    pts = sorted((r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == 1 and r == c)
    T = {}
    if len(pts) < 2:
        return T
    # constant diagonal step between consecutive markers
    step = pts[1][0] - pts[0][0]
    if step <= 0:
        return T
    # continue the arithmetic sequence beyond the last marker with color 2
    r = pts[-1][0] + step
    while r < H and r < W:
        if input_grid[r][r] == 0:
            T[(r, r)] = 2
        r += step
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
