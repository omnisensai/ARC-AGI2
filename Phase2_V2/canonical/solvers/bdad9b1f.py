"""Canonical solver for ARC puzzle bdad9b1f.

Rule: the grid contains two short colored line segments on a background of 0:
one made of color 8 and one made of color 2. Each segment lies along a single
axis (all in one column, or all in one row). Each segment is extended into a
full crossing line spanning the whole grid along its perpendicular axis -- a
column-aligned segment becomes a full column, a row-aligned segment becomes a
full row. Where the extended 8-line and 2-line intersect, the cell becomes 4.
"""


def _segment_axis(cells):
    """Return ('col', c) if all cells share a column, else ('row', r)."""
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(cols) == 1:
        return ('col', next(iter(cols)))
    if len(rows) == 1:
        return ('row', next(iter(rows)))
    # Fallback: pick the more constrained axis.
    if len(cols) <= len(rows):
        return ('col', next(iter(cols)))
    return ('row', next(iter(rows)))


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    eights = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    twos = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]

    T = {}
    if not eights or not twos:
        return T

    axis8, idx8 = _segment_axis(eights)
    axis2, idx2 = _segment_axis(twos)

    def extend(axis, idx, color):
        if axis == 'col':
            for r in range(H):
                T[(r, idx)] = color
        else:
            for c in range(W):
                T[(idx, c)] = color

    extend(axis8, idx8, 8)
    extend(axis2, idx2, 2)

    # Intersection cell of the two full lines becomes 4.
    r4 = idx8 if axis8 == 'row' else (idx2 if axis2 == 'row' else None)
    c4 = idx8 if axis8 == 'col' else (idx2 if axis2 == 'col' else None)
    if r4 is not None and c4 is not None:
        T[(r4, c4)] = 4

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
