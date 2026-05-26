"""Canonical solver for ARC puzzle 7d419a02.

Structure
---------
The grid is a field of 8-colored blocks.  One axis is partitioned by 0-separator
lines into several strips (the *separated* axis); the other axis runs
continuously (the *tiled* axis).  Exactly one block is painted with the marker
color 6; that marker block defines a center and a size `s` (its extent along the
tiled axis).

Rule
----
A "bow-tie"/double-cone opens outward from the marker block along the tiled axis.
For a strip at cell-distance `d` (>= 1) from the marker's strip along the
separated axis, an 8-pixel whose tiled coordinate `t` lies OUTSIDE the band

    [ six_lo - s*(d-1) ,  six_hi + s*(d-1) ]

is recolored to 4.  Pixels inside the band, and the marker's own strip (d == 0),
keep color 8.  The mask `T` records exactly the cells that turn into 4.
"""


def _segments(seps, n):
    """Cell spans (a, b) between separator coordinates over an axis of length n."""
    bounds = sorted(set([-1] + seps + [n]))
    segs = []
    for i in range(len(bounds) - 1):
        a = bounds[i] + 1
        b = bounds[i + 1] - 1
        if a <= b:
            segs.append((a, b))
    return segs


def infer_T(input_grid):
    """Latent mask: dict {(r, c): 4} of 8-pixels to repaint to 4."""
    H = len(input_grid)
    W = len(input_grid[0])

    sep_rows = [r for r in range(H) if all(v == 0 for v in input_grid[r])]
    sep_cols = [c for c in range(W) if all(input_grid[r][c] == 0 for r in range(H))]

    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    if not sixes:
        return {}
    rs = [r for r, _ in sixes]
    cs = [c for _, c in sixes]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    rsegs = _segments(sep_rows, H)
    csegs = _segments(sep_cols, W)
    rows_separated = len(rsegs) > 1
    cols_separated = len(csegs) > 1

    T = {}

    if rows_separated and not cols_separated:
        # rows = separated axis, cols = tiled axis
        s = c1 - c0 + 1                      # marker size along tiled axis
        six_strip = next(i for i, (a, b) in enumerate(rsegs) if a <= r0 <= b)
        for i, (ra, rb) in enumerate(rsegs):
            d = abs(i - six_strip)
            if d == 0:
                continue
            lo = c0 - s * (d - 1)
            hi = c1 + s * (d - 1)
            for r in range(ra, rb + 1):
                for c in range(W):
                    if input_grid[r][c] == 8 and not (lo <= c <= hi):
                        T[(r, c)] = 4
    elif cols_separated and not rows_separated:
        # cols = separated axis, rows = tiled axis
        s = r1 - r0 + 1                      # marker size along tiled axis
        six_strip = next(j for j, (a, b) in enumerate(csegs) if a <= c0 <= b)
        for j, (ca, cb) in enumerate(csegs):
            d = abs(j - six_strip)
            if d == 0:
                continue
            lo = r0 - s * (d - 1)
            hi = r1 + s * (d - 1)
            for c in range(ca, cb + 1):
                for r in range(H):
                    if input_grid[r][c] == 8 and not (lo <= r <= hi):
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
