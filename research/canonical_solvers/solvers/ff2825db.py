"""Canonical solver for ARC task ff2825db.

Structure: a 10x10 grid whose top row (row 0) is a legend, with a solid frame
(rows 1 & H-2 border, cols of the inner region) drawn in some border color, and
a 0-background interior holding scattered cells of exactly two colors. The more
frequent ("majority") scattered color is the dominant one. The transformation:
recolor the whole frame to the majority color, erase every scattered cell, and
draw a rectangle outline (in the majority color) at the bounding box of the
majority-color cells. The legend row is left untouched.
"""


def _components_colors(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cells = {}
    # interior excludes the legend row (0), the frame rows (1, H-2..) and frame cols.
    for r in range(2, H - 1):
        for c in range(1, W - 1):
            v = input_grid[r][c]
            if v != 0:
                cells.setdefault(v, []).append((r, c))
    return cells


def infer_T(input_grid):
    """Return a latent mask dict {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    cells = _components_colors(input_grid)
    if not cells:
        return T

    # majority scattered color
    maj = max(cells, key=lambda k: len(cells[k]))
    pts = cells[maj]

    # bounding box of the majority-color cells
    r0 = min(p[0] for p in pts)
    r1 = max(p[0] for p in pts)
    c0 = min(p[1] for p in pts)
    c1 = max(p[1] for p in pts)

    # 1) erase every scattered cell in the interior (set to background 0)
    for r in range(2, H - 1):
        for c in range(1, W - 1):
            if input_grid[r][c] != 0:
                T[(r, c)] = 0

    # 2) recolor the frame to the majority color.
    #    The frame = the ring of cells (rows 1..H-1, cols 0..W-1) that are
    #    currently the border color (i.e. non-zero and on the outer ring,
    #    excluding the legend row 0).
    border_color = input_grid[1][0]
    for r in range(1, H):
        for c in range(W):
            if input_grid[r][c] == border_color and (
                r == 1 or r == H - 1 or c == 0 or c == W - 1
            ):
                T[(r, c)] = maj

    # 3) draw a rectangle outline at the majority bounding box.
    for c in range(c0, c1 + 1):
        T[(r0, c)] = maj
        T[(r1, c)] = maj
    for r in range(r0, r1 + 1):
        T[(r, c0)] = maj
        T[(r, c1)] = maj

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
