"""Canonical latent-T solver for ARC puzzle e734a0e8.

Rule: the grid is partitioned into equal cells by full separator lines (color 0).
One cell holds a multi-pixel colored template shape; other cells each hold a
single isolated marker dot (color 0) inside the cell interior. The template is
stamped (at identical cell-relative coordinates) into every marked cell,
overwriting the marker.
"""


def _separators(grid):
    H, W = len(grid), len(grid[0])
    sep_rows = [r for r in range(H) if all(v == 0 for v in grid[r])]
    sep_cols = [c for c in range(W) if all(grid[r][c] == 0 for r in range(H))]
    return sep_rows, sep_cols


def _ranges(seps, n):
    res, start = [], 0
    for s in seps + [n]:
        if s > start:
            res.append((start, s - 1))
        start = s + 1
    return res


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    """Return a latent transformation mask dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    sep_rows, sep_cols = _separators(input_grid)
    row_blocks = _ranges(sep_rows, H)
    col_blocks = _ranges(sep_cols, W)
    bg = _background(input_grid)

    template = None       # list of (dr, dc, color) relative to cell origin
    marker_cells = []     # list of (r0, c0, [(dr,dc)...]) cells with marker dots

    for (r0, r1) in row_blocks:
        for (c0, c1) in col_blocks:
            colored = []   # non-background, non-zero pixels
            zeros = []     # interior zero markers
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    v = input_grid[r][c]
                    if v == 0:
                        zeros.append((r - r0, c - c0))
                    elif v != bg:
                        colored.append((r - r0, c - c0, v))
            if len(colored) >= 2:
                template = colored
            if len(zeros) == 1 and not colored:
                marker_cells.append((r0, c0, zeros))

    T = {}
    if template is None:
        return T
    for (r0, c0, zeros) in marker_cells:
        # erase the marker dot to background first
        for (dr, dc) in zeros:
            T[(r0 + dr, c0 + dc)] = bg
        # then stamp the template
        for (dr, dc, color) in template:
            T[(r0 + dr, c0 + dc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
