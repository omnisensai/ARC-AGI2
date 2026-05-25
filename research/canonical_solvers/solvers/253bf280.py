def infer_T(input_grid):
    """Latent mask: cells strictly between adjacent collinear pairs of 8s
    (same row or same column, nothing between them) get color 3."""
    H, W = len(input_grid), len(input_grid[0])
    eights = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    T = {}
    by_row = {}
    for r, c in eights:
        by_row.setdefault(r, []).append(c)
    for r, cs in by_row.items():
        cs = sorted(cs)
        for i in range(len(cs) - 1):
            c1, c2 = cs[i], cs[i + 1]
            if c2 - c1 > 1:
                for c in range(c1 + 1, c2):
                    T[(r, c)] = 3
    by_col = {}
    for r, c in eights:
        by_col.setdefault(c, []).append(r)
    for c, rs in by_col.items():
        rs = sorted(rs)
        for i in range(len(rs) - 1):
            r1, r2 = rs[i], rs[i + 1]
            if r2 - r1 > 1:
                for r in range(r1 + 1, r2):
                    T[(r, c)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
