"""Canonical solver for ARC puzzle 981add89.

Rule: row 0 holds single-cell colored markers on a background. Each marker
shoots a vertical ray straight down its column. Along that column the ray
repaints every cell below row 0:
  - if the cell already has the marker's own color (it lies inside a block of
    that same color), it is set to the background (the ray "cuts a gap");
  - otherwise (background cell, or a block of a different color) it is set to
    the marker color.
The marker cell in row 0 itself is left unchanged.

infer_T builds the explicit overwrite mask {(r,c): new_color}; apply_T copies
the input and writes only those masked cells.
"""

from collections import Counter


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = {}  # latent mask: (r, c) -> new color
    for c in range(W):
        marker = input_grid[0][c]
        if marker == bg:
            continue  # no ray emitted from a background cell in row 0
        for r in range(1, H):
            cell = input_grid[r][c]
            if cell == marker:
                T[(r, c)] = bg
            else:
                T[(r, c)] = marker
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
