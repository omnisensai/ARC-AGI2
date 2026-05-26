"""Canonical ARC solver for puzzle da2b0fe3.

Rule: the non-zero shape has a one-cell-wide empty gap (a fully empty row or
column inside its bounding box) that splits it into two mirror halves. Extend
that gap line across the entire grid, filling it with color 3.
"""


def infer_T(input_grid):
    """Infer the latent transformation mask: cells to paint with color 3.

    Returns a dict {(r, c): 3} for every cell on the extended symmetry-gap line.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    T = {}
    if not cells:
        return T

    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    # Empty columns (vertical gap) inside the bounding box.
    empty_cols = [
        c for c in range(c0, c1 + 1)
        if all(input_grid[r][c] == bg for r in range(r0, r1 + 1))
    ]
    # Empty rows (horizontal gap) inside the bounding box.
    empty_rows = [
        r for r in range(r0, r1 + 1)
        if all(input_grid[r][c] == bg for c in range(c0, c1 + 1))
    ]

    for c in empty_cols:
        for r in range(H):
            T[(r, c)] = 3
    for r in empty_rows:
        for c in range(W):
            T[(r, c)] = 3

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
