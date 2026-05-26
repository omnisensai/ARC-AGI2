"""Canonical solver for ARC puzzle 984d8a3e.

Each row is three horizontal bands: a left band of color L (variable width),
a middle fill band of color F (the most common color), and a right band of
color R. The right band is fixed. The fill block is slid LEFT until its right
edge reaches a global target column T (the minimum fill-right-edge over all
rows), limited by the amount of L material available. The L cells displaced
from the left edge re-appear as a band immediately to the left of the R band.
"""

from collections import Counter


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    F = cnt.most_common(1)[0][0]                      # fill color (most common)
    L = Counter(row[0] for row in input_grid if row[0] != F).most_common(1)[0][0]
    R = Counter(row[-1] for row in input_grid if row[-1] != F).most_common(1)[0][0]

    def left_width(row):
        n = 0
        for v in row:
            if v == L:
                n += 1
            else:
                break
        return n

    def right_width(row):
        n = 0
        for v in reversed(row):
            if v == R:
                n += 1
            else:
                break
        return n

    # Target: the leftmost fill-block right edge among all rows.
    target_edge = min(W - right_width(row) for row in input_grid)

    T = {}  # latent mask: {(r, c): new_color}
    for r in range(H):
        row = input_grid[r]
        lwi = left_width(row)
        fill_right = W - right_width(row)
        # Shift the fill block left by `inner`, bounded by available L cells.
        inner = min(lwi, fill_right - target_edge)
        if inner <= 0:
            continue
        # Left L cells that are vacated become fill.
        for c in range(lwi - inner, lwi):
            T[(r, c)] = F
        # The displaced L cells form a band just before the R band.
        for c in range(fill_right - inner, fill_right):
            T[(r, c)] = L
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
