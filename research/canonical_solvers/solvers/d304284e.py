"""Canonical solver for ARC puzzle d304284e.

Rule: the input contains a single glyph (a connected set of non-background
cells) inside a bounding box. The glyph is stamped repeatedly on a tiling
grid whose horizontal pitch is (bbox_width + 1) and vertical pitch is
(bbox_height + 1), anchored at the glyph's original top-left position and
extending to the right and downward across the grid.

Tile columns repeat a 7,7,6 color cycle: columns whose tile-index mod 3 == 2
are "accent" columns drawn in the accent color (6); the other columns are
drawn in the glyph's own color. In the anchor (top) tile-row every column is
stamped; in the rows below only the accent columns continue downward.
"""

ACCENT = 6


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    if not cells:
        return {}, bg

    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    bh = r1 - r0 + 1
    bw = c1 - c0 + 1

    # glyph color (most common non-bg color inside the box)
    fcounts = {}
    for r, c in cells:
        v = input_grid[r][c]
        fcounts[v] = fcounts.get(v, 0) + 1
    glyph_color = max(fcounts, key=fcounts.get)

    # relative shape footprint inside its bounding box
    shape = [(r - r0, c - c0) for r, c in cells]

    sh = bh + 1   # vertical pitch
    sw = bw + 1   # horizontal pitch

    T = {}

    # enumerate tile columns to the right (anchor at tile index 0)
    tc = 0
    while c0 + tc * sw < W:
        accent = (tc % 3 == 2)
        color = ACCENT if accent else glyph_color
        bc = c0 + tc * sw

        # tile rows: anchor row always; rows below only for accent columns
        tr = 0
        while r0 + tr * sh < H:
            if tr == 0 or accent:
                br = r0 + tr * sh
                for dr, dc in shape:
                    rr, cc = br + dr, bc + dc
                    if 0 <= rr < H and 0 <= cc < W:
                        T[(rr, cc)] = color
            tr += 1
        tc += 1

    return T, bg


def apply_T(input_grid, T):
    mask, _bg = T
    out = [row[:] for row in input_grid]
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
