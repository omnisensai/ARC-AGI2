def infer_T(input_grid):
    """Find every axis-aligned rectangle whose 4 corners are color-4 cells with
    an empty (no interior 4) strict interior, and mark that interior to be 2."""
    H, W = len(input_grid), len(input_grid[0])
    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    fourset = set(fours)
    rows = sorted(set(r for r, c in fours))
    cols = sorted(set(c for r, c in fours))
    T = {}
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            for a in range(len(cols)):
                for b in range(a + 1, len(cols)):
                    c1, c2 = cols[a], cols[b]
                    if not ((r1, c1) in fourset and (r1, c2) in fourset and
                            (r2, c1) in fourset and (r2, c2) in fourset):
                        continue
                    interior = [(r, c) for r in range(r1 + 1, r2)
                                for c in range(c1 + 1, c2)]
                    if not interior:
                        continue
                    if any((r, c) in fourset for r, c in interior):
                        continue
                    for r, c in interior:
                        T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
