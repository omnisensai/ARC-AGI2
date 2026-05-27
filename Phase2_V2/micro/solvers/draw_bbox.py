from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    col = g[cells[0][0]][cells[0][1]]
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    T = {}
    for c in range(c0, c1 + 1):
        if g[r0][c] == bg: T[(r0, c)] = col
        if g[r1][c] == bg: T[(r1, c)] = col
    for r in range(r0, r1 + 1):
        if g[r][c0] == bg: T[(r, c0)] = col
        if g[r][c1] == bg: T[(r, c1)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
