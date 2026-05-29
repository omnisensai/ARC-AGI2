from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seeds = sorted((r, c) for r in range(H) for c in range(W) if g[r][c] != bg)
    if len(seeds) < 2:
        return {}
    col = g[seeds[0][0]][seeds[0][1]]
    if any(g[r][c] != col for r, c in seeds):
        return {}
    T = {}
    for i in range(len(seeds) - 1):
        r1, c1 = seeds[i]; r2, c2 = seeds[i + 1]
        # horizontal then vertical from (r1, c1) to (r2, c2)
        step_c = 1 if c2 > c1 else (-1 if c2 < c1 else 0)
        if step_c:
            for c in range(c1 + step_c, c2 + step_c, step_c):
                if (r1, c) not in set(seeds) and (r1, c) not in T:
                    T[(r1, c)] = col
                elif (r1, c) in set(seeds):
                    pass  # already this colour
        step_r = 1 if r2 > r1 else (-1 if r2 < r1 else 0)
        if step_r:
            for r in range(r1 + step_r, r2 + step_r, step_r):
                if (r, c2) not in set(seeds) and (r, c2) not in T:
                    T[(r, c2)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
