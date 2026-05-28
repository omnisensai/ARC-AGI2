from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bv]
    T = {}
    if not cells:
        return T
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    for c in range(c0, c1 + 1):
        T[(r0, c)] = 1; T[(r1, c)] = 1        # top + bottom edges
    for r in range(r0, r1 + 1):
        T[(r, c0)] = 1; T[(r, c1)] = 1        # left + right edges
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
