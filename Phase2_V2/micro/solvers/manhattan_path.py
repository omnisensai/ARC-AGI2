from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != bg]
    if len(nz) != 2:
        return {}
    (r1, c1, _), (r2, c2, _) = nz
    col = nz[0][2]
    if r1 == r2 or c1 == c2:
        return {}  # collinear -> not this family's rule
    # Sort endpoints: A = (smaller row, tiebreak smaller col)
    if (r1, c1) > (r2, c2):
        r1, c1, r2, c2 = r2, c2, r1, c1
    # L: horizontal from (r1, c1) -> (r1, c2), then vertical to (r2, c2).
    T = {}
    step_c = 1 if c2 > c1 else -1
    for c in range(c1 + step_c, c2 + step_c, step_c):
        T[(r1, c)] = col
    step_r = 1 if r2 > r1 else -1
    for r in range(r1 + step_r, r2 + step_r, step_r):
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
