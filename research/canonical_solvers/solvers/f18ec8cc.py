"""Canonical solver for ARC task f18ec8cc.

The grid is partitioned into vertical panels: maximal runs of consecutive
columns that share the same dominant (background) color.  The transformation
reverses the left-to-right order of these panels while preserving each panel's
internal contents (including any noise cells).  Panel widths are preserved, so
the output dimensions equal the input dimensions.

infer_T computes the column permutation (panel-reversal) and emits a latent
mask: a dict mapping each cell whose color changes to its new color.
apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _column_panels(grid):
    """Group columns into panels by per-column dominant color runs."""
    H = len(grid)
    W = len(grid[0])
    col_bg = []
    for c in range(W):
        cnt = Counter(grid[r][c] for r in range(H))
        col_bg.append(cnt.most_common(1)[0][0])
    panels = []
    start = 0
    for c in range(1, W):
        if col_bg[c] != col_bg[start]:
            panels.append((start, c - 1))
            start = c
    panels.append((start, W - 1))
    return panels


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    panels = _column_panels(input_grid)

    # Build the column permutation: panels in reversed order, each panel's
    # columns kept in their original internal left-to-right order.
    src_cols = []
    for (a, b) in reversed(panels):
        src_cols.extend(range(a, b + 1))
    # dest column i is filled from src_cols[i]
    col_map = {dest: src for dest, src in enumerate(src_cols)}

    # Latent mask: only cells whose value changes.
    T = {}
    for r in range(H):
        for dest in range(W):
            src = col_map[dest]
            new_val = input_grid[r][src]
            if new_val != input_grid[r][dest]:
                T[(r, dest)] = new_val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
