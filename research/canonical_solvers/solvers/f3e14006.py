"""Canonical latent-T solver for ARC puzzle f3e14006.

Structure of every pair: the input contains one long horizontal line (a row that
is almost entirely filled) and one long vertical line (a column that is almost
entirely filled) that cross.  Each line is drawn in a single "base" colour but
carries exactly two "marker" cells of a different colour.

The transformation erases both lines and, in a rectangular region, weaves the two
lines into a plaid:

  * The region spans, in columns, the interval between the two horizontal markers
    (these become the outer "data" columns); in rows it spans from the crossing
    row out to the farther of the two vertical markers.
  * Rows/cols measured from the crossing row / the marker edge alternate between
    "data" lines (even offset) and "separator" lines (odd offset).
  * data-row x data-col  -> a marker colour: the horizontal marker colour for the
    rows nearer the crossing than the near vertical marker, else the vertical
    marker colour.
  * separator-row x data-col -> horizontal base colour.
  * data-row x separator-col -> vertical base colour (but the row sitting exactly
    on the near vertical marker is overwritten with the horizontal base colour
    when the horizontal line is the one drawn on top at the crossing).
  * separator-row x separator-col -> whichever base belongs to the line that is
    drawn on top at the crossing cell (horizontal-base if the crossing shows the
    horizontal base, otherwise vertical-base).

`infer_T` derives this geometry from the input alone and returns a latent mask
(dict {(r,c): new_colour}) of every cell that must change; `apply_T` copies the
input and overwrites only the masked cells.
"""

from collections import Counter


def _lines(g):
    """Return (hrow, vcol): the dominant horizontal and vertical line indices."""
    H, W = len(g), len(g[0])
    row_nz = [sum(1 for v in g[r] if v != 0) for r in range(H)]
    col_nz = [sum(1 for r in range(H) if g[r][c] != 0) for c in range(W)]
    hrow = max(range(H), key=lambda r: row_nz[r])
    vcol = max(range(W), key=lambda c: col_nz[c])
    return hrow, vcol


def _base_and_marks(vals, exclude_idx):
    """Given the colours along a line (excluding the crossing index), return the
    base colour (most common nonzero) and the sorted list of marker indices."""
    cnt = Counter(v for i, v in enumerate(vals) if i != exclude_idx and v != 0)
    base = cnt.most_common(1)[0][0]
    marks = sorted(i for i, v in enumerate(vals)
                   if i != exclude_idx and v != 0 and v != base)
    return base, marks


def infer_T(input_grid):
    """Infer the latent transformation mask from the input structure."""
    g = input_grid
    H, W = len(g), len(g[0])
    hrow, vcol = _lines(g)

    vvals = [g[r][vcol] for r in range(H)]
    hvals = g[hrow]
    vbase, vmarks = _base_and_marks(vvals, hrow)
    hbase, hmarks = _base_and_marks(hvals, vcol)

    T = {}
    # Degenerate input (missing a proper two-marker line): no change.
    if len(vmarks) < 2 or len(hmarks) < 2:
        return T

    vmark_color = vvals[vmarks[0]]
    hmark_color = hvals[hmarks[0]]

    near_v = min(abs(m - hrow) for m in vmarks)   # near vertical-marker distance
    far_v_row = max(vmarks, key=lambda m: abs(m - hrow))

    # Row span: from the crossing row out to the farther vertical marker.
    r0, r1 = min(hrow, far_v_row), max(hrow, far_v_row)
    # Column span: the interval bounded by the two horizontal markers.
    c0, c1 = min(hmarks), max(hmarks)

    # Which line is drawn on top at the crossing cell?
    h_on_top = (g[hrow][vcol] == hbase)

    # 1) Erase every original line cell (turns to background 0).
    for r in range(H):
        if g[r][vcol] != 0:
            T[(r, vcol)] = 0
    for c in range(W):
        if g[hrow][c] != 0:
            T[(hrow, c)] = 0

    # 2) Paint the woven plaid block.
    for r in range(r0, r1 + 1):
        dr = abs(r - hrow)          # rows measured from the crossing (a data line)
        rt = dr % 2                 # 0 = data row, 1 = separator row
        for c in range(c0, c1 + 1):
            ct = (c - c0) % 2       # 0 = data col, 1 = separator col
            if rt == 0 and ct == 0:
                color = hmark_color if dr < near_v else vmark_color
            elif rt == 0 and ct == 1:
                color = vbase
                if h_on_top and dr == near_v:
                    color = hbase
            elif rt == 1 and ct == 0:
                color = hbase
            else:
                color = hbase if h_on_top else vbase
            T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
