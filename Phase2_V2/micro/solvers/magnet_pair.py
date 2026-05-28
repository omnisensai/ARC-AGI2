from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if len(nz) != 2:
        return {}
    (r1, c1), (r2, c2) = sorted(nz)
    col = g[r1][c1]
    if g[r2][c2] != col:
        return {}
    T = {}
    if r1 == r2 and c2 - c1 >= 2:
        new_c1 = (c1 + c2) // 2; new_c2 = new_c1 + 1
        if c1 != new_c1: T[(r1, c1)] = bg
        if c2 != new_c2: T[(r2, c2)] = bg
        T[(r1, new_c1)] = col; T[(r2, new_c2)] = col
    elif c1 == c2 and r2 - r1 >= 2:
        new_r1 = (r1 + r2) // 2; new_r2 = new_r1 + 1
        if r1 != new_r1: T[(r1, c1)] = bg
        if r2 != new_r2: T[(r2, c2)] = bg
        T[(new_r1, c1)] = col; T[(new_r2, c2)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
