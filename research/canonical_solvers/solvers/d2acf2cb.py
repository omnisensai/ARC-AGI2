"""Canonical solver for ARC puzzle d2acf2cb.

Rule: pairs of 4-markers (two 4s in the same row, or two 4s in the same
column) define a line segment.  The cells strictly between the two markers
get their color toggled under the involution 6<->7, 0<->8.  This recolors a
"plain" segment (6/0) into its accented form (7/8) and vice versa.
"""

# Involution applied to the interior cells of a 4..4 segment.
_TOGGLE = {6: 7, 7: 6, 0: 8, 8: 0}


def _marker_positions(grid):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 4]


def infer_T(input_grid):
    """Return a latent transformation mask {(r,c): new_color}.

    The 4-markers sit on a pair of opposite borders.  If they line the
    left/right edge columns the segments run horizontally (row by row); if
    they line the top/bottom edge rows the segments run vertically (column by
    column).  Every interior cell between the two markers of a segment is
    toggled under the involution 6<->7, 0<->8.
    """
    H, W = len(input_grid), len(input_grid[0])
    markers = _marker_positions(input_grid)

    marker_cols = set(c for _, c in markers)
    marker_rows = set(r for r, _ in markers)

    # Orientation: markers on the left/right edges -> horizontal segments;
    # markers on the top/bottom edges -> vertical segments.
    on_lr_edges = marker_cols <= {0, W - 1} and marker_cols == {0, W - 1}
    on_tb_edges = marker_rows <= {0, H - 1} and marker_rows == {0, H - 1}

    T = {}

    def toggle_interior(cells):
        for (r, c) in cells:
            v = input_grid[r][c]
            if v in _TOGGLE:
                T[(r, c)] = _TOGGLE[v]

    if on_lr_edges:
        # Horizontal segments: consecutive marker pairs in each row.
        by_row = {}
        for (r, c) in markers:
            by_row.setdefault(r, []).append(c)
        for r, cols in by_row.items():
            cols = sorted(cols)
            for a, b in zip(cols, cols[1:]):
                toggle_interior((r, c) for c in range(a + 1, b))
    elif on_tb_edges:
        # Vertical segments: consecutive marker pairs in each column.
        by_col = {}
        for (r, c) in markers:
            by_col.setdefault(c, []).append(r)
        for c, rows in by_col.items():
            rows = sorted(rows)
            for a, b in zip(rows, rows[1:]):
                toggle_interior((r, c) for r in range(a + 1, b))

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
