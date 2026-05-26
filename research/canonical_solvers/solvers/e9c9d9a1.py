"""Canonical solver for ARC puzzle e9c9d9a1.

The grid is partitioned into a block matrix by full rows/columns of the
separator color (3). For the resulting BR x BC block grid:
  - the four corner blocks are recolored 2 (top-left), 4 (top-right),
    1 (bottom-left), 8 (bottom-right);
  - every strictly interior block is recolored 7;
  - all other (non-corner border) blocks are left unchanged.
Only the background cells inside each block are overwritten; the separator
lines are preserved.
"""


def _block_segments(length, full_lines):
    segs = []
    prev = 0
    for ln in full_lines + [length]:
        if ln > prev:
            segs.append((prev, ln))
        prev = ln + 1
    return segs


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Detect the separator color: the value that fills entire rows or columns.
    sep = None
    for v in range(10):
        if any(all(input_grid[r][c] == v for c in range(W)) for r in range(H)) or \
           any(all(input_grid[r][c] == v for r in range(H)) for c in range(W)):
            sep = v
            break

    T = [[None] * W for _ in range(H)]
    if sep is None:
        return T

    full_r = [r for r in range(H) if all(input_grid[r][c] == sep for c in range(W))]
    full_c = [c for c in range(W) if all(input_grid[r][c] == sep for r in range(H))]

    row_segs = _block_segments(H, full_r)
    col_segs = _block_segments(W, full_c)
    BR, BC = len(row_segs), len(col_segs)
    if BR == 0 or BC == 0:
        return T

    def fill(r0, r1, c0, c1, color):
        for r in range(r0, r1):
            for c in range(c0, c1):
                if input_grid[r][c] != sep:
                    T[r][c] = color

    for bi, (r0, r1) in enumerate(row_segs):
        for bj, (c0, c1) in enumerate(col_segs):
            top = bi == 0
            bottom = bi == BR - 1
            left = bj == 0
            right = bj == BC - 1
            color = None
            if top and left:
                color = 2
            elif top and right:
                color = 4
            elif bottom and left:
                color = 1
            elif bottom and right:
                color = 8
            elif not (top or bottom or left or right):
                color = 7
            if color is not None:
                fill(r0, r1, c0, c1, color)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for r in range(len(out)):
        for c in range(len(out[0])):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
