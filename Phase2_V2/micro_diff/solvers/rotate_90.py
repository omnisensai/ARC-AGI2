def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": W, "w": H}                       # dims swap


def apply_T(g, T):
    H = len(g)
    return [[g[H - 1 - j][i] for j in range(T["w"])] for i in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
