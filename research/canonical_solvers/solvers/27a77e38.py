def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): color}.

    Structure: a grid of colored cells sits at the top, followed by a full
    row of 5s acting as a divider, then a block of 0s below it. The rule
    places a single cell at the bottom-most row, in the middle column, whose
    color is the most frequent color appearing in the top grid (the region
    above the divider row of 5s).
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Locate the divider: the first full row of 5s.
    div = None
    for r in range(H):
        if all(v == 5 for v in input_grid[r]):
            div = r
            break

    # Region above the divider is the colored source grid.
    top_rows = range(div) if div is not None else range(H)

    counts = {}
    for r in top_rows:
        for c in range(W):
            v = input_grid[r][c]
            counts[v] = counts.get(v, 0) + 1

    T = {}
    if not counts:
        return T

    # Most frequent color in the top grid (ties broken by smallest color).
    best = max(counts, key=lambda v: (counts[v], -v))

    # Place it at the last row, middle column.
    T[(H - 1, W // 2)] = best
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
