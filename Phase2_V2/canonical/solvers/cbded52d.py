"""Canonical solver for ARC task cbded52d.

Structure: the grid is split by full single-color separator lines into a 3x3
arrangement of small blocks (each block is a sub-grid of identical dims). Within
the blocks there is a dominant fill color plus sparse "marker" cells.

Rule (latent T): consider every line of three collinear blocks (each block-row
and each block-column). If the two END blocks of a line both carry the same
marker color at the same in-block sub-position, then the MIDDLE block of that
line receives that marker at that sub-position. Original cells are preserved;
only the inferred middle-block cells are overwritten.
"""

from collections import Counter


def _segments(n, seps):
    """Contiguous index runs of [0,n) excluding separator indices in `seps`."""
    res, s = [], 0
    for x in range(n):
        if x in seps:
            if s < x:
                res.append((s, x))
            s = x + 1
    if s < n:
        res.append((s, n))
    return res


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    # Separator lines: full rows / columns of a single constant color.
    sep_rows = [r for r in range(H) if len(set(g[r])) == 1]
    sep_cols = [c for c in range(W) if len({g[r][c] for r in range(H)}) == 1]
    sep_vals = {g[r][0] for r in sep_rows} | {g[0][c] for c in sep_cols}

    rsegs = _segments(H, set(sep_rows))
    csegs = _segments(W, set(sep_cols))
    nbr, nbc = len(rsegs), len(csegs)

    # Dominant fill color (ignoring separator colors).
    inner = [v for row in g for v in row if v not in sep_vals]
    T = {}
    if not inner:
        return T
    fill = Counter(inner).most_common(1)[0][0]

    def marks(bi, bj):
        r0, r1 = rsegs[bi]
        c0, c1 = csegs[bj]
        m = {}
        for r in range(r0, r1):
            for c in range(c0, c1):
                v = g[r][c]
                if v not in sep_vals and v != fill:
                    m[(r - r0, c - c0)] = v
        return m

    # Block-rows: ends at columns 0 and nbc-1, middle column = 1 (only 3 blocks).
    if nbc == 3:
        for bi in range(nbr):
            a, b = marks(bi, 0), marks(bi, 2)
            r0, _ = rsegs[bi]
            c0, _ = csegs[1]
            for sub, col in a.items():
                if b.get(sub) == col:
                    T[(r0 + sub[0], c0 + sub[1])] = col

    # Block-columns: ends at rows 0 and nbr-1, middle row = 1 (only 3 blocks).
    if nbr == 3:
        for bj in range(nbc):
            a, b = marks(0, bj), marks(2, bj)
            r0, _ = rsegs[1]
            c0, _ = csegs[bj]
            for sub, col in a.items():
                if b.get(sub) == col:
                    T[(r0 + sub[0], c0 + sub[1])] = col

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
