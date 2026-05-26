def infer_T(input_grid):
    """Infer the latent colouring mask.

    The grid is a lattice of 3x3 boxes (drawn in 8) separated by gridlines
    (rows/cols containing no 8). Each non-background, non-8 colour appears as
    marker cells. The markers of one colour, snapped to the nearest gridlines,
    define a rectangular lattice region. That region is painted in the colour:
      - its top/bottom boundary gridlines (between the two corner separators)
      - its left/right boundary gridlines
      - the centre cell of every 3x3 box strictly inside the region
    """
    H, W = len(input_grid), len(input_grid[0])

    sep_rows = [r for r in range(H) if not any(input_grid[r][c] == 8 for c in range(W))]
    sep_cols = [c for c in range(W) if not any(input_grid[r][c] == 8 for r in range(H))]

    def snap(x, seps):
        return min(seps, key=lambda s: (abs(s - x), s))

    markers = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v != 8:
                markers.setdefault(v, []).append((r, c))

    T = {}
    for color, pts in markers.items():
        rs = [snap(r, sep_rows) for r, c in pts]
        cs = [snap(c, sep_cols) for r, c in pts]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # boundary gridlines of the rectangle
        for c in range(c0, c1 + 1):
            T[(r0, c)] = color
            T[(r1, c)] = color
        for r in range(r0, r1 + 1):
            T[(r, c0)] = color
            T[(r, c1)] = color

        # centre of each 3x3 box fully inside the rectangle
        i0, i1 = sep_rows.index(r0), sep_rows.index(r1)
        j0, j1 = sep_cols.index(c0), sep_cols.index(c1)
        for ii in range(i0, i1):
            for jj in range(j0, j1):
                cr = (sep_rows[ii] + sep_rows[ii + 1]) // 2
                cc = (sep_cols[jj] + sep_cols[jj + 1]) // 2
                T[(cr, cc)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
