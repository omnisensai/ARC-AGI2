def infer_T(input_grid):
    """Find full rows and full columns consisting entirely of the line color.

    Each grid has a dominant foreground color and color 0. Some complete rows
    and/or complete columns are made up entirely of 0 (the line color). Those
    cells become the marker color 2.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # The line color is 0 in every observed pair; identify it generically as
    # the value that forms at least one complete row or complete column.
    candidates = set()
    for r in range(H):
        vals = set(input_grid[r])
        if len(vals) == 1:
            candidates.add(next(iter(vals)))
    for c in range(W):
        vals = set(input_grid[r][c] for r in range(H))
        if len(vals) == 1:
            candidates.add(input_grid[0][c])

    T = {}
    if not candidates:
        return T

    # Pick the line color: the candidate that is NOT the most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    line_candidates = [v for v in candidates if v != bg]
    if not line_candidates:
        line_candidates = list(candidates)

    marker = 2
    for line_color in line_candidates:
        for r in range(H):
            if all(input_grid[r][c] == line_color for c in range(W)):
                for c in range(W):
                    T[(r, c)] = marker
        for c in range(W):
            if all(input_grid[r][c] == line_color for r in range(H)):
                for r in range(H):
                    T[(r, c)] = marker
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
