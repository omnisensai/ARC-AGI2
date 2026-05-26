"""Canonical solver for ARC puzzle e3fe1151.

Rule
----
A full row and a full column painted in a single separator color form a cross
that divides the grid into rectangular quadrant regions.  Inside the quadrants
the separator color appears again as "holes".  Every quadrant is meant to hold
the SAME multiset of colors; the holes are filled with whatever color(s) are
missing from a quadrant relative to the shared consensus multiset.

`infer_T` derives the latent mask {(r,c): color} of holes-to-fill purely from
the input.  `apply_T` copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _separator_color(grid):
    """The color that fills at least one entire row AND one entire column."""
    H, W = len(grid), len(grid[0])
    full_row_colors = set()
    for r in range(H):
        vals = set(grid[r])
        if len(vals) == 1:
            full_row_colors.add(next(iter(vals)))
    full_col_colors = set()
    for c in range(W):
        vals = set(grid[r][c] for r in range(H))
        if len(vals) == 1:
            full_col_colors.add(next(iter(vals)))
    common = full_row_colors & full_col_colors
    if not common:
        return None
    # Prefer the color forming the most separator lines (a stable choice).
    def line_count(col):
        rc = sum(1 for r in range(H) if all(v == col for v in grid[r]))
        cc = sum(1 for c in range(W)
                 if all(grid[r][c] == col for r in range(H)))
        return rc + cc
    return max(common, key=line_count)


def _quadrant_regions(grid, sep):
    """Split the grid into blocks of cells separated by full sep lines."""
    H, W = len(grid), len(grid[0])
    sep_rows = set(r for r in range(H) if all(v == sep for v in grid[r]))
    sep_cols = set(c for c in range(W)
                   if all(grid[r][c] == sep for r in range(H)))
    # Contiguous runs of non-separator rows / cols define block bands.
    def bands(n, seps):
        bands, cur = [], []
        for i in range(n):
            if i in seps:
                if cur:
                    bands.append(cur)
                    cur = []
            else:
                cur.append(i)
        if cur:
            bands.append(cur)
        return bands

    row_bands = bands(H, sep_rows)
    col_bands = bands(W, sep_cols)
    regions = []
    for rb in row_bands:
        for cb in col_bands:
            regions.append([(r, c) for r in rb for c in cb])
    return regions


def infer_T(input_grid):
    """Return a latent transformation mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    sep = _separator_color(input_grid)
    if sep is None:
        return T

    regions = _quadrant_regions(input_grid, sep)
    if len(regions) < 2:
        return T

    # Known (non-hole) color multiset per region.
    known = []
    for cells in regions:
        kn = Counter(input_grid[r][c] for (r, c) in cells
                     if input_grid[r][c] != sep)
        known.append(kn)

    # Consensus multiset: per-color maximum count seen across regions.
    consensus = Counter()
    for kn in known:
        for v, ct in kn.items():
            if ct > consensus[v]:
                consensus[v] = ct

    # Fill each region's holes with the colors it is missing from consensus.
    for cells, kn in zip(regions, known):
        holes = [(r, c) for (r, c) in cells if input_grid[r][c] == sep]
        if not holes:
            continue
        missing = list((consensus - kn).elements())
        if len(missing) != len(holes):
            # Ambiguous / structure does not match expectation: skip safely.
            continue
        for (r, c), color in zip(holes, missing):
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
