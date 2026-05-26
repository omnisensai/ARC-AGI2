from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for c in range(W):
        col_vals = [g[r][c] for r in range(H)]
        items = [v for v in col_vals if v != bg]
        new = [bg] * (H - len(items)) + items
        for r in range(H):
            if new[r] != col_vals[r]:
                T[(r, c)] = new[r]
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
