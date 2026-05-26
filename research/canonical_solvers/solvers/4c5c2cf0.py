"""Canonical solver for ARC puzzle 4c5c2cf0.

Rule
----
Each grid contains two colored objects on a 0 background:
  * a "marker": an X-shaped 5-cell object (the four corners and the centre of a
    3x3 box, relative cells {(-1,-1),(-1,1),(0,0),(1,-1),(1,1)}). Its centre is
    the point of symmetry and it is left unchanged.
  * a "payload": the other colored object.

The payload is reflected about the marker centre across the horizontal axis,
the vertical axis, and both axes (a 4-fold mirror). The union of the four
reflected copies (original included) is stamped onto the grid.

infer_T builds the latent mask of the new payload cells; apply_T overwrites them.
"""

# X marker pattern: relative offsets of the 5 cells about its centre.
MARKER = frozenset({(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)})


def _cells_by_color(grid):
    H, W = len(grid), len(grid[0])
    by = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 0:
                by.setdefault(v, []).append((r, c))
    return by


def _find_marker(by_color):
    """Return (marker_color, (cr, cc)) for the X-shaped object, else None."""
    for col, cells in by_color.items():
        if len(cells) != 5:
            continue
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        cr = (min(rs) + max(rs)) // 2
        cc = (min(cs) + max(cs)) // 2
        rel = frozenset((r - cr, c - cc) for r, c in cells)
        if rel == MARKER:
            return col, (cr, cc)
    return None


def infer_T(input_grid):
    """Latent mask: {(r, c): color} of payload cells to draw (4-fold mirror)."""
    by = _cells_by_color(input_grid)
    found = _find_marker(by)
    if found is None:
        return {}
    mcol, (mr, mc) = found

    payload_colors = [c for c in by if c != mcol]
    if not payload_colors:
        return {}
    pcol = payload_colors[0]
    payload = by[pcol]

    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r, c in payload:
        for rr, cc in (
            (r, c),
            (r, 2 * mc - c),
            (2 * mr - r, c),
            (2 * mr - r, 2 * mc - c),
        ):
            if 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = pcol
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
