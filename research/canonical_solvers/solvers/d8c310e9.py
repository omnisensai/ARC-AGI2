"""Canonical solver for ARC puzzle d8c310e9.

Rule: the grid contains a horizontally periodic column-pattern anchored at the
left edge. Only part of the width is drawn (the rightmost copy may be
truncated, the rest of the grid is background). Recover the column period P from
the drawn region, then tile the pattern across the FULL width so that every
column c takes the column-template at index (c % P). Cells whose target value
differs from the current value form the latent transformation mask.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _columns(grid, H, W):
    return [[grid[r][c] for r in range(H)] for c in range(W)]


def _period(cols, last):
    """Smallest P s.t. drawn columns 0..last equal the tiling of cols[0:P]."""
    for cand in range(1, len(cols) + 1):
        if all(cols[c] == cols[c % cand] for c in range(last + 1)):
            return cand
    return len(cols)


def infer_T(input_grid):
    """Return a latent transformation mask {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    cols = _columns(input_grid, H, W)

    nonbg = [c for c in range(W) if any(v != bg for v in cols[c])]
    T = {}
    if not nonbg:
        return T

    last = max(nonbg)
    P = _period(cols, last)

    for c in range(W):
        src = c % P
        for r in range(H):
            new_color = input_grid[r][src]
            if new_color != input_grid[r][c]:
                T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
