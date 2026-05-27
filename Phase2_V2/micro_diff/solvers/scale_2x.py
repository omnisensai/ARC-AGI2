def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": 2 * H, "w": 2 * W}


def apply_T(g, T):
    return [[g[r // 2][c // 2] for c in range(T["w"])] for r in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
