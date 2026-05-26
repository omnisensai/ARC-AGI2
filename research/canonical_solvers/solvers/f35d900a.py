"""Canonical solver for ARC task f35d900a.

Structure: four single-cell markers sit at the corners of an axis-aligned
rectangle. Opposite corners share a color, so exactly two colors appear.
Each marker expands into a 3x3 box whose border is the *other* color and whose
center is the marker's own color. Dotted "5" lines run along the marker rows
and columns through the gap between the boxes, with dots placed at the two
cells nearest each box (offsets 0 and 2 from the box edge).
"""


def _markers(grid):
    H, W = len(grid), len(grid[0])
    return [(r, c, grid[r][c]) for r in range(H) for c in range(W) if grid[r][c] != 0]


def _line_offsets(L):
    """Dot offsets within an inner gap of length L (cells between two boxes)."""
    s = set()
    for o in (0, 2):
        if 0 <= o < L:
            s.add(o)
    for o in (L - 1, L - 3):
        if 0 <= o < L:
            s.add(o)
    return s


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    ms = _markers(input_grid)
    if len(ms) != 4:
        return T

    rows = sorted(set(m[0] for m in ms))
    cols = sorted(set(m[1] for m in ms))
    if len(rows) != 2 or len(cols) != 2:
        return T
    colors = set(m[2] for m in ms)
    if len(colors) != 2:
        return T
    r0, r1 = rows
    c0, c1 = cols

    # marker color lookup
    mc = {(r, c): v for r, c, v in ms}

    # 3x3 boxes: border = other color, center = own color
    for (r, c), own in mc.items():
        other = next(x for x in colors if x != own)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = own if (dr == 0 and dc == 0) else other

    # horizontal dotted lines along each marker row, between the two boxes
    gapc_start, gapc_end = c0 + 2, c1 - 2  # inclusive inner gap (cols)
    Lh = gapc_end - gapc_start + 1
    if Lh > 0:
        offs = _line_offsets(Lh)
        for r in (r0, r1):
            for o in offs:
                cc = gapc_start + o
                if (r, cc) not in T:
                    T[(r, cc)] = 5

    # vertical dotted lines along each marker column, between the two boxes
    gapr_start, gapr_end = r0 + 2, r1 - 2  # inclusive inner gap (rows)
    Lv = gapr_end - gapr_start + 1
    if Lv > 0:
        offs = _line_offsets(Lv)
        for c in (c0, c1):
            for o in offs:
                rr = gapr_start + o
                if (rr, c) not in T:
                    T[(rr, c)] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
