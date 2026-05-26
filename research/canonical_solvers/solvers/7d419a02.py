"""Canonical solver for ARC puzzle 7d419a02.

Structure: the grid is a field of 8-blocks (cells), 2x2 each, laid out on a
regular lattice.  One axis carries explicit 0-separator lines (cell + 1-pixel
gap), the other axis tiles contiguously.  Exactly one cell is painted with the
marker color 6 (a 2x2 block).

Rule (a "bow-tie"/cone opening along the tiled axis, centered on the 6 cell):
let `a` be a cell's signed cell-index displacement from the 6 cell along the
*tiled* axis and `b` the displacement along the *separated* axis.  A cell's
8-pixels are recolored to 4 iff  |a| >= |b|  and  b != 0.  The 6 cell and the
whole separated-axis line through it are left untouched.
"""


def _axis_segments(seps, start6, size, n):
    """Return (list of (a,b) cell spans, is_separated_axis)."""
    bounds = sorted(set([-1] + seps + [n]))
    segs = []
    for i in range(len(bounds) - 1):
        a = bounds[i] + 1
        b = bounds[i + 1] - 1
        if a <= b:
            segs.append((a, b))
    if len(segs) > 1:
        return segs, True  # explicit separators -> separated axis
    # single contiguous span: tile by `size`, aligned with the marker cell
    lo, hi = segs[0]
    cc = start6
    while cc - size >= lo:
        cc -= size
    res = []
    while cc + size - 1 <= hi:
        res.append((cc, cc + size - 1))
        cc += size
    return res, False  # tiled axis


def infer_T(input_grid):
    """Compute the latent recolor mask: dict {(r,c): 4} for cells to repaint."""
    H = len(input_grid)
    W = len(input_grid[0])

    sep_rows = [r for r in range(H) if all(v == 0 for v in input_grid[r])]
    sep_cols = [c for c in range(W) if all(input_grid[r][c] == 0 for r in range(H))]

    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    if not sixes:
        return {}
    rs = [r for r, _ in sixes]
    cs = [c for _, c in sixes]
    r0, c0 = min(rs), min(cs)
    ch = max(rs) - min(rs) + 1
    cw = max(cs) - min(cs) + 1

    rsegs, rsep = _axis_segments(sep_rows, r0, ch, H)
    csegs, csep = _axis_segments(sep_cols, c0, cw, W)

    si = next(i for i, (a, b) in enumerate(rsegs) if a <= r0 <= b)
    sj = next(j for j, (a, b) in enumerate(csegs) if a <= c0 <= b)

    T = {}
    for i, (ra, rb) in enumerate(rsegs):
        for j, (ca, cb) in enumerate(csegs):
            di = i - si
            dj = j - sj
            if di == 0 and dj == 0:
                continue  # the marker cell itself
            # `a` along tiled axis, `b` along separated axis
            if not rsep:        # rows tiled, cols separated
                a, b = di, dj
            else:               # cols tiled, rows separated
                a, b = dj, di
            if abs(a) >= abs(b) and b != 0:
                for r in range(ra, rb + 1):
                    for c in range(ca, cb + 1):
                        if input_grid[r][c] == 8:
                            T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
