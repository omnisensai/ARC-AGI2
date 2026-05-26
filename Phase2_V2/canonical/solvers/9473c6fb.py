def infer_T(input_grid):
    """Recolor each marker cell (non-background) with a repeating [2,8,5] cycle.

    The markers lie along a dominant axis. We order them along that axis
    (row-major if there are more distinct marker rows than columns, else
    column-major) and assign colors cycling 2 -> 8 -> 5 in sequence.
    Returns the latent mask as {(r, c): new_color}.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background is the most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Marker cells.
    cells = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg]
    if not cells:
        return {}

    distinct_rows = len(set(r for r, c in cells))
    distinct_cols = len(set(c for r, c in cells))

    # Order along the dominant axis.
    if distinct_rows >= distinct_cols:
        cells.sort(key=lambda rc: (rc[0], rc[1]))   # row-major
    else:
        cells.sort(key=lambda rc: (rc[1], rc[0]))   # column-major

    cycle = [2, 8, 5]
    T = {}
    for i, (r, c) in enumerate(cells):
        T[(r, c)] = cycle[i % len(cycle)]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
