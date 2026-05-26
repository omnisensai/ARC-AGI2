from collections import Counter
from math import gcd


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        pts = [c for c in range(W) if g[r][c] != bg]
        if len(pts) < 2:
            continue
        col = g[r][pts[0]]
        p = 0
        for i in range(len(pts) - 1):
            p = gcd(p, pts[i + 1] - pts[i])
        if p < 1:
            continue
        phase = pts[0] % p
        for c in range(W):
            if c % p == phase and g[r][c] == bg:
                T[(r, c)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
