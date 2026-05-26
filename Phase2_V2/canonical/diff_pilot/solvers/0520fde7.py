def infer_T(g):
    H, W = len(g), len(g[0])
    sep = next(c for c in range(W)
               if len({g[r][c] for r in range(H)}) == 1 and g[0][c] != 0)
    return {"sep": sep, "h": H, "w": sep}    # output = left-half dims


def apply_T(g, T):
    sep = T["sep"]
    left = [row[:sep] for row in g]
    right = [row[sep + 1:] for row in g]
    h, w = len(left), len(left[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if left[r][c] != 0 and right[r][c] != 0:   # AND of the two halves
                out[r][c] = 2
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
