"""Canonical solver for ARC task e729b7be.

Structure: a full vertical "axis" column (color 4) carries a single marker
cell (color 8). The same color 8 also marks the two grid borders on one row,
defining a horizontal axis. Their intersection (8 on the axis column) is a
rotation center. A colored shape sits against the axis on its left side.

Rule: reflect/rotate the left shape 180 degrees about the intersection center;
the rotated copy lands on the right side of the axis. Background and axis cells
stay; only the destination cells (initially background) are overwritten.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_axis(grid, bg):
    """Return (axis_col, marker_color, line_color) for the vertical line column.

    The axis is a full-height column made of a single line color (not the
    background) plus exactly one differing marker cell.
    """
    H, W = len(grid), len(grid[0])
    for c in range(W):
        col = [grid[r][c] for r in range(H)]
        vals = set(col)
        if len(vals) != 2:
            continue
        for marker in vals:
            line = (vals - {marker}).pop()
            if line == bg:
                continue
            if col.count(marker) == 1 and col.count(line) == H - 1:
                return c, marker, line
    return None


def infer_T(input_grid):
    """Latent mask: dict {(r,c): new_color} for cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    axis_info = _find_axis(input_grid, bg)
    T = {}
    if axis_info is None:
        return T
    axis_col, marker, line = axis_info
    # rotation center: the marker cell on the axis column
    cr = next(r for r in range(H) if input_grid[r][axis_col] == marker)
    cc = axis_col

    # determine which side the source shape occupies (the non-background side)
    left_cells = sum(
        1
        for r in range(H)
        for c in range(axis_col)
        if input_grid[r][c] not in (bg, marker, line)
    )
    right_cells = sum(
        1
        for r in range(H)
        for c in range(axis_col + 1, W)
        if input_grid[r][c] not in (bg, marker, line)
    )

    if left_cells >= right_cells:
        src_cols = range(axis_col)
    else:
        src_cols = range(axis_col + 1, W)

    for r in range(H):
        for c in src_cols:
            v = input_grid[r][c]
            if v in (bg, marker, line):
                continue
            # rotate 180 about center
            nr = 2 * cr - r
            nc = 2 * cc - c
            if 0 <= nr < H and 0 <= nc < W:
                # only overwrite cells that are currently background
                if input_grid[nr][nc] == bg:
                    T[(nr, nc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
