"""Canonical latent-T solver for ARC puzzle e7dd8335.

Rule: a single shape drawn in color 1 occupies some vertical bounding-box
span. The lower half of that span (the bottom floor(span/2) rows of the
bounding box) has its 1-cells recolored to 2; the upper half is left as 1.
The transformation mask marks exactly those bottom-half foreground cells.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Determine background as the most frequent color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Foreground = all non-background cells (the shape, color 1).
    fg = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]

    T = {}
    if not fg:
        return T

    rmin = min(r for r, _ in fg)
    rmax = max(r for r, _ in fg)
    span = rmax - rmin + 1
    bottom_count = span // 2
    # Boundary: rows strictly in the lower half of the span.
    threshold = rmax - bottom_count + 1

    for (r, c) in fg:
        if r >= threshold:
            T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
