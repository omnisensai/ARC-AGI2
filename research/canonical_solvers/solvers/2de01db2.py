"""Canonical solver for ARC puzzle 2de01db2.

Rule (per row): each row holds a dominant non-zero color plus background
zeros and scattered "noise" colors. The transformation inverts the dominant
color's mask within the row: cells holding the dominant color become 0, and
every other cell (zeros and noise) becomes the dominant color.

T is the latent change mask: T[r][c] is the new color for any cell that
differs from the input, else None. apply_T overwrites only masked cells.
"""

from collections import Counter


def _dominant_color(row):
    """The most frequent non-zero color in the row (ties broken by lower id)."""
    counts = Counter(v for v in row if v != 0)
    if not counts:
        return None
    return max(counts, key=lambda k: (counts[k], -k))


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        dom = _dominant_color(input_grid[r])
        if dom is None:
            continue
        for c in range(W):
            # invert the dominant-color mask for this row
            new = 0 if input_grid[r][c] == dom else dom
            if new != input_grid[r][c]:
                T[r][c] = new
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
