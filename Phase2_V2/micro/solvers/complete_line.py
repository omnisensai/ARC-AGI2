from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    pts = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    (r1, c1), (r2, c2) = pts[0], pts[-1]
    col = g[r1][c1]
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    T = {}
    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2) and 0 <= r < H and 0 <= c < W:
        T[(r, c)] = col
        r += dr
        c += dc
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
