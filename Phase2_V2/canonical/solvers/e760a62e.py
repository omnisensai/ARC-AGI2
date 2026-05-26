"""Canonical solver for ARC task e760a62e.

Structure: the grid is partitioned into rectangular cells by full lines of a
separator color (8). A few cells contain a single colored marker dot. Each
color has several markers; every pair of markers of the same color that share
a cell-row or cell-column draws the inclusive segment of cells between them,
filling each spanned cell entirely with that color. Where segments of two
different colors overlap, the overlapped cell becomes 6.

infer_T derives, from the input alone, a per-cell color mask (the latent T).
apply_T copies the input and overwrites only the data area of masked cells.
"""


def _full_lines(grid):
    """Return (sep_color, rows_that_are_full_lines, cols_that_are_full_lines)."""
    H, W = len(grid), len(grid[0])
    # The separator color is the one forming full rows/cols. Find candidate.
    sep = None
    for r in range(H):
        v = grid[r][0]
        if all(grid[r][c] == v for c in range(W)):
            sep = v
            break
    if sep is None:
        for c in range(W):
            v = grid[0][c]
            if all(grid[r][c] == v for r in range(H)):
                sep = v
                break
    if sep is None:
        return None, [], []
    rows = [r for r in range(H) if all(grid[r][c] == sep for c in range(W))]
    cols = [c for c in range(W) if all(grid[r][c] == sep for r in range(H))]
    return sep, rows, cols


def _blocks(length, lines):
    """Ranges of consecutive non-line indices, given sorted separator lines."""
    blocks = []
    prev = 0
    for x in list(lines) + [length]:
        if x > prev:
            blocks.append((prev, x))
        prev = x + 1
    return blocks


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sep, rows8, cols8 = _full_lines(input_grid)
    if sep is None:
        return {"cells": {}, "rb": [(0, H)], "cb": [(0, W)]}
    rb = _blocks(H, rows8)
    cb = _blocks(W, cols8)

    # Find marker color per cell (any cell-interior color that is not sep / bg).
    # Background is the most common color inside cells.
    counts = {}
    for r0, r1 in rb:
        for c0, c1 in cb:
            for r in range(r0, r1):
                for c in range(c0, c1):
                    v = input_grid[r][c]
                    counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get) if counts else 0

    markers = {}  # color -> list of (ri, ci)
    for ri, (r0, r1) in enumerate(rb):
        for ci, (c0, c1) in enumerate(cb):
            found = None
            for r in range(r0, r1):
                for c in range(c0, c1):
                    v = input_grid[r][c]
                    if v != bg and v != sep:
                        found = v
                        break
                if found is not None:
                    break
            if found is not None:
                markers.setdefault(found, []).append((ri, ci))

    # For each color, draw inclusive cell-segments between every pair of
    # markers that share a cell-row or cell-column.
    color_cells = {}  # color -> set of (ri, ci)
    for color, pts in markers.items():
        cells = set()
        n = len(pts)
        for i in range(n):
            for j in range(i + 1, n):
                (ar, ac), (br, bc) = pts[i], pts[j]
                if ar == br:
                    lo, hi = sorted((ac, bc))
                    for c in range(lo, hi + 1):
                        cells.add((ar, c))
                elif ac == bc:
                    lo, hi = sorted((ar, br))
                    for r in range(lo, hi + 1):
                        cells.add((r, ac))
        color_cells[color] = cells

    # Resolve per-cell color: overlap of two distinct colors -> 6.
    cell_color = {}
    overlap = set()
    for color, cells in color_cells.items():
        for cell in cells:
            if cell in cell_color and cell_color[cell] != color:
                overlap.add(cell)
            else:
                cell_color[cell] = color
    for cell in overlap:
        cell_color[cell] = 6

    return {"cells": cell_color, "rb": rb, "cb": cb}


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    rb = T["rb"]
    cb = T["cb"]
    for (ri, ci), color in T["cells"].items():
        r0, r1 = rb[ri]
        c0, c1 = cb[ci]
        for r in range(r0, r1):
            for c in range(c0, c1):
                out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
