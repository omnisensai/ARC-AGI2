from collections import Counter

NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and g[r + dr][c + dc] != bg
                                     for dr, dc in NB):
                T[(r, c)] = 8                 # fixed fence colour, 4-connected (open corners)
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
