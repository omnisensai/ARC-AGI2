from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    delta = (H - 1) - max(r for r, c in cells)
    T = {}
    for (r, c) in cells:
        T[(r, c)] = bg                       # erase old position
    for (r, c) in cells:
        T[(r + delta, c)] = g[r][c]          # draw at new position (overrides erase)
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
