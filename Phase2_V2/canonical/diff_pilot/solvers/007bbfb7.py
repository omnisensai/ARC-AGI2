def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": H * H, "w": W * W}          # 3x3 -> 9x9 fractal self-tiling


def apply_T(g, T):
    H, W = len(g), len(g[0])
    out = [[0] * (W * W) for _ in range(H * H)]
    for R in range(H):
        for C in range(W):
            if g[R][C] != 0:                 # block "on" -> stamp the whole grid
                for r in range(H):
                    for c in range(W):
                        out[R * H + r][C * W + c] = g[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
