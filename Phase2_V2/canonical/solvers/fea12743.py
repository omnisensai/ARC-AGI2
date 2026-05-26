"""Canonical latent-T solver for ARC puzzle fea12743.

Structure of every grid: a background (color 0) lattice divides the grid into a
set of equally sized rectangular "cells", each containing one shape drawn in a
single foreground color (color 2).  The shapes are detected by their bounding
blocks (groups of rows / columns that contain foreground separated by fully
background rows / columns).

Rule (inferred from all train + test pairs):
  * Measure the foreground pixel count (area) of every cell-shape.
  * Exactly one shape has a UNIQUE area (it is the "reference": a larger shape
    that is the superposition of two of the ordinary shapes).  That reference
    cell is recoloured 3.
  * The two ordinary cells whose pixel-wise UNION reproduces the reference shape
    (in place, same orientation) are recoloured 8.  (If several such pairs exist
    because two ordinary shapes are identical, the first pair in reading order is
    used.)
  * Every other cell keeps its colour.

infer_T builds a transformation mask {(r,c): new_color}; apply_T copies the
input and overwrites only the masked cells.
"""

from collections import Counter
from itertools import combinations


def _find_bands(present):
    """Given a list of booleans (True = line contains foreground), return the
    list of (start, end_exclusive) index ranges of maximal True runs."""
    bands = []
    i = 0
    n = len(present)
    while i < n:
        if present[i]:
            j = i
            while j < n and present[j]:
                j += 1
            bands.append((i, j))
            i = j
        else:
            i += 1
    return bands


def _cells(grid):
    """Locate the rectangular cell blocks (separated by all-background lines).

    Returns dict {(band_row, band_col): (r0, r1, c0, c1)} bounding boxes."""
    H, W = len(grid), len(grid[0])
    # most common color is treated as background
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    row_has = [any(grid[r][c] != bg for c in range(W)) for r in range(H)]
    col_has = [any(grid[r][c] != bg for r in range(H)) for c in range(W)]
    rbands = _find_bands(row_has)
    cbands = _find_bands(col_has)
    cells = {}
    for ri, (r0, r1) in enumerate(rbands):
        for ci, (c0, c1) in enumerate(cbands):
            # only keep blocks that actually contain foreground
            if any(grid[r][c] != bg for r in range(r0, r1) for c in range(c0, c1)):
                cells[(ri, ci)] = (r0, r1, c0, c1)
    return cells, bg


def _shape(grid, box, bg):
    r0, r1, c0, c1 = box
    return tuple(
        tuple(1 if grid[r][c] != bg else 0 for c in range(c0, c1))
        for r in range(r0, r1)
    )


def _union(a, b):
    return tuple(
        tuple(1 if a[i][j] or b[i][j] else 0 for j in range(len(a[0])))
        for i in range(len(a))
    )


def infer_T(input_grid):
    """Return a latent mask: dict {(r, c): new_color} for cells to overwrite."""
    cells, bg = _cells(input_grid)
    T = {}
    if not cells:
        return T

    shapes = {k: _shape(input_grid, cells[k], bg) for k in cells}
    # ensure all shapes share the same dimensions (required for union); if not,
    # there is nothing meaningful to do.
    dims = {(len(s), len(s[0])) for s in shapes.values()}
    if len(dims) != 1:
        return T

    areas = {k: sum(sum(row) for row in shapes[k]) for k in cells}
    area_counts = Counter(areas.values())

    # reference cell: the one whose area is unique
    unique_areas = [a for a, n in area_counts.items() if n == 1]
    if len(unique_areas) != 1:
        return T
    ref_area = unique_areas[0]
    ref_cells = [k for k in cells if areas[k] == ref_area]
    if len(ref_cells) != 1:
        return T
    ref = ref_cells[0]
    ref_shape = shapes[ref]

    others = [k for k in cells if k != ref]

    # find pair of ordinary cells whose pixel-wise union reproduces reference
    def mark(box, color):
        r0, r1, c0, c1 = box
        for r in range(r0, r1):
            for c in range(c0, c1):
                if input_grid[r][c] != bg:
                    T[(r, c)] = color

    chosen = None
    for a, b in combinations(others, 2):
        if _union(shapes[a], shapes[b]) == ref_shape:
            chosen = (a, b)
            break  # reading-order-first deterministic tiebreak

    # reference becomes 3
    mark(cells[ref], 3)
    if chosen is not None:
        mark(cells[chosen[0]], 8)
        mark(cells[chosen[1]], 8)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
