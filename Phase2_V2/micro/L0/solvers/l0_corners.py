def infer_T(g):
    H, W = len(g), len(g[0])
    T = {}
    for (r, c) in [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]:
        T[(r, c)] = 1                       # MARK
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
