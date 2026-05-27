from collections import Counter

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    sr, sc = cells[0]; S = g[sr][sc]
    T = {}
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while 0 <= r < H and 0 <= c < W:
            if g[r][c] == bg:
                T[(r, c)] = S
            r += dr; c += dc
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
