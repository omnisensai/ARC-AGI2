"""Canonical ARC solver for puzzle ded97339.

Rule: the grid contains isolated single-cell markers of one foreground color
on a background. Any two markers that share the same row or the same column are
connected by a straight line segment (the cells strictly between them, and the
endpoints, are painted the foreground color). Markers that align with no other
marker stay isolated.
"""


def infer_T(input_grid):
    """Infer the latent transformation mask from input structure alone.

    Returns a dict {(r, c): new_color} of cells to overwrite.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Determine background = most frequent color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return {}
    bg = max(counts, key=counts.get)

    # Collect marker cells (any non-background cell).
    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W)
               if input_grid[r][c] != bg]

    T = {}

    # For every pair of markers sharing a row, draw the horizontal segment.
    # For every pair sharing a column, draw the vertical segment.
    n = len(markers)
    for i in range(n):
        r1, c1, col1 = markers[i]
        for j in range(i + 1, n):
            r2, c2, col2 = markers[j]
            if r1 == r2:
                lo, hi = sorted((c1, c2))
                for c in range(lo, hi + 1):
                    T[(r1, c)] = col1
            if c1 == c2:
                lo, hi = sorted((r1, r2))
                for r in range(lo, hi + 1):
                    T[(r, c1)] = col1

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
