from collections import Counter


def _path_8conn(p1, p2):
    """8-conn path from p1 to p2 (exclusive of p1, inclusive of p2):
    diagonal steps first, then axis-aligned for the remainder."""
    r, c = p1
    r2, c2 = p2
    dr = (r2 > r) - (r2 < r)
    dc = (c2 > c) - (c2 < c)
    path = []
    while r != r2 and c != c2:
        r += dr; c += dc
        path.append((r, c))
    while r != r2:
        r += dr
        path.append((r, c))
    while c != c2:
        c += dc
        path.append((r, c))
    return path


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seeds = sorted((r, c) for r in range(H) for c in range(W) if g[r][c] != bg)
    if len(seeds) < 2:
        return {}
    col = g[seeds[0][0]][seeds[0][1]]
    if any(g[r][c] != col for r, c in seeds):
        return {}
    seeds_set = set(seeds)
    T = {}
    for i in range(len(seeds) - 1):
        for cell in _path_8conn(seeds[i], seeds[i + 1]):
            if cell not in seeds_set and cell not in T:
                T[cell] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
