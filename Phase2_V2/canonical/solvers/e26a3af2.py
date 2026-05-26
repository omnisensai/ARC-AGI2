"""Canonical ARC solver for puzzle e26a3af2.

Rule: the grid is partitioned into parallel stripes (either every column or
every row) where each stripe is dominated by a single background color and a
few scattered "noise" cells of other colors. The transformation replaces every
noise cell with its stripe's dominant (majority) color, leaving each stripe
uniform. Orientation (column-stripes vs row-stripes) is detected from the input
by whichever orientation yields purer (more uniform) stripes.
"""

from collections import Counter


def _stripes(grid, orient):
    H, W = len(grid), len(grid[0])
    if orient == 'col':
        return [Counter(grid[r][c] for r in range(H)) for c in range(W)]
    return [Counter(grid[r]) for r in range(H)]


def _purity(stripes):
    total = sum(sum(c.values()) for c in stripes)
    if total == 0:
        return 0.0
    return sum(c.most_common(1)[0][1] for c in stripes) / total


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cols = _stripes(input_grid, 'col')
    rows = _stripes(input_grid, 'row')
    orient = 'col' if _purity(cols) >= _purity(rows) else 'row'
    stripes = cols if orient == 'col' else rows
    dom = [c.most_common(1)[0][0] for c in stripes]

    # Latent mask: only cells differing from their stripe's dominant color.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            d = dom[c] if orient == 'col' else dom[r]
            if input_grid[r][c] != d:
                T[r][c] = d
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
