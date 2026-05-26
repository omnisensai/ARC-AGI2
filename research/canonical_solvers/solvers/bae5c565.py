def infer_T(input_grid):
    """Infer the latent transformation mask.

    Row 0 holds a horizontal 'key' palette. One column contains a vertical
    line of 8s starting at some row r_top and running to the bottom; this is
    the spout of a pyramid. The pyramid grows upward from the bottom: column c
    starts at row r_top + |c - c8| and is filled to the bottom with key[c]
    (the 8-column itself is filled with 8). Every other cell becomes the
    background color.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    key = input_grid[0]

    # Locate the 8 column and the top of the 8 line.
    c8 = None
    for c in range(W):
        if any(input_grid[r][c] == 8 for r in range(1, H)):
            c8 = c
            break
    if c8 is None:
        return {"bg": bg, "cells": {}}

    r_top = min(r for r in range(1, H) if input_grid[r][c8] == 8)

    # Build the mask: every cell first defaults to bg, then the pyramid paints.
    cells = {}
    for r in range(H):
        for c in range(W):
            cells[(r, c)] = bg

    for c in range(W):
        start = r_top + abs(c - c8)
        color = 8 if c == c8 else key[c]
        for r in range(start, H):
            cells[(r, c)] = color

    return {"bg": bg, "cells": cells}


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    cells = T["cells"]
    for (r, c), v in cells.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
