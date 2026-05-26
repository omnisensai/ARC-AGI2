from collections import Counter


def _find_band(g):
    """Locate the solid 5-band: a maximal set of full columns or full rows of 5s.
    Returns (orient, lo, hi) where orient is 'V' (vertical columns) or 'H' (rows)."""
    H, W = len(g), len(g[0])
    cols = [c for c in range(W) if all(g[r][c] == 5 for r in range(H))]
    rows = [r for r in range(H) if all(g[r][c] == 5 for c in range(W))]
    if cols:
        return ('V', min(cols), max(cols))
    if rows:
        return ('H', min(rows), max(rows))
    return None


def _marker_color(g):
    """Most common non-zero, non-5 color = the marker color."""
    c = Counter()
    for row in g:
        for v in row:
            if v not in (0, 5):
                c[v] += 1
    return c.most_common(1)[0][0] if c else None


def infer_T(input_grid):
    """Build the latent mask {(r,c): new_color}.

    Rule: a solid 5-band runs across the grid (a strip of full columns OR full
    rows). Scattered single-cell markers sit to either side of the band. Each
    marker is removed (-> 0). For every row (vertical band) or column (horizontal
    band), the band grows toward each side by exactly the number of markers on
    that side of the band in that line: the next N cells out from the band edge
    become 5.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    band = _find_band(input_grid)
    mc = _marker_color(input_grid)
    if band is None or mc is None:
        return T
    orient, lo, hi = band

    # Remove all markers.
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == mc:
                T[(r, c)] = 0

    if orient == 'V':
        for r in range(H):
            ln = sum(1 for c in range(0, lo) if input_grid[r][c] == mc)
            rn = sum(1 for c in range(hi + 1, W) if input_grid[r][c] == mc)
            for k in range(1, ln + 1):
                if lo - k >= 0:
                    T[(r, lo - k)] = 5
            for k in range(1, rn + 1):
                if hi + k < W:
                    T[(r, hi + k)] = 5
    else:  # 'H'
        for c in range(W):
            tn = sum(1 for r in range(0, lo) if input_grid[r][c] == mc)
            bn = sum(1 for r in range(hi + 1, H) if input_grid[r][c] == mc)
            for k in range(1, tn + 1):
                if lo - k >= 0:
                    T[(lo - k, c)] = 5
            for k in range(1, bn + 1):
                if hi + k < H:
                    T[(hi + k, c)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
