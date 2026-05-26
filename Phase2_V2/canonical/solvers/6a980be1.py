def _period(seq):
    n = len(seq)
    for p in range(1, n + 1):
        if all(seq[i] == seq[i % p] for i in range(n)):
            return p
    return n


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    border = input_grid[0][0]
    LINE = 3
    fill = 2

    rmin = rmax = cmin = cmax = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != border:
                if rmin is None or r < rmin: rmin = r
                if rmax is None or r > rmax: rmax = r
                if cmin is None or c < cmin: cmin = c
                if cmax is None or c > cmax: cmax = c

    horiz_lines = [r for r in range(rmin, rmax + 1)
                   if all(input_grid[r][c] == LINE for c in range(cmin, cmax + 1))]
    vert_lines = [c for c in range(cmin, cmax + 1)
                  if all(input_grid[r][c] == LINE for r in range(rmin, rmax + 1))]

    if len(horiz_lines) >= 2:
        orient = 'H'
        a, b = min(horiz_lines), max(horiz_lines)
    else:
        orient = 'V'
        a, b = min(vert_lines), max(vert_lines)

    T = [[None] * W for _ in range(H)]

    if orient == 'V':
        interior_cols = list(range(a + 1, b))
        known_rows = sorted(r for r in range(H) if input_grid[r][a] == LINE)
        seq = [any(input_grid[r][cc] == fill for cc in interior_cols) for r in known_rows]
        period = _period(seq)
        base = known_rows[0]
        for r in range(H):
            isfilled = seq[(r - base) % period]
            for c in range(W):
                if a <= c <= b:
                    T[r][c] = LINE if (c == a or c == b) else (fill if isfilled else 0)
                else:
                    T[r][c] = border if isfilled else 0
    else:
        interior_rows = list(range(a + 1, b))
        known_cols = sorted(c for c in range(W) if input_grid[a][c] == LINE)
        seq = [any(input_grid[rr][c] == fill for rr in interior_rows) for c in known_cols]
        period = _period(seq)
        base = known_cols[0]
        for c in range(W):
            isfilled = seq[(c - base) % period]
            for r in range(H):
                if a <= r <= b:
                    T[r][c] = LINE if (r == a or r == b) else (fill if isfilled else 0)
                else:
                    T[r][c] = border if isfilled else 0
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
