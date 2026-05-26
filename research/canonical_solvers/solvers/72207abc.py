def infer_T(input_grid):
    """Infer the latent mask of cells to fill.

    The active row holds a seed of colored cells starting at column 0. The
    spacing between the last two seed cells defines a gap that then grows by 1
    for each subsequent placement, cycling through the seed colors until the
    next position would fall off the grid.
    """
    H, W = len(input_grid), len(input_grid[0])
    # locate the active row (the one containing non-background cells)
    bg = 0
    arow = None
    for r in range(H):
        if any(input_grid[r][c] != bg for c in range(W)):
            arow = r
            break
    T = {}
    if arow is None:
        return T
    seed = [(c, input_grid[arow][c]) for c in range(W) if input_grid[arow][c] != bg]
    if not seed:
        return T
    cols = [c for c, _ in seed]
    colors = [v for _, v in seed]
    last = cols[-1]
    gap = cols[-1] - cols[-2] if len(cols) >= 2 else 1
    pos = last
    i = 0
    while True:
        gap += 1
        pos += gap
        if pos >= W:
            break
        T[(arow, pos)] = colors[i % len(colors)]
        i += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
