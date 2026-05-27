def infer_T(g):
    H, W = len(g), len(g[0])
    T = {}
    for r in range(H):
        for c in range(W):
            mc = W - 1 - c
            if g[r][c] != g[r][mc]:
                T[(r, c)] = g[r][mc]
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
