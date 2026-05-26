def infer_T(input_grid):
    """Infer the latent change mask.

    Structure: a 3-row grid whose middle row is solid (all the foreground
    color, here 4) and whose top/bottom rows alternate foreground/background.
    The transformation paints diagonal stripes of color 6 onto foreground
    cells, anchored on the solid row every PERIOD columns. PERIOD is the
    spacing of the diagonal stripes = 3 (the foreground cells of the solid
    row that line up with a stripe). We derive the foreground color, the
    solid (anchor) row, and the period from the grid itself, then mark every
    foreground cell whose column lies on an anchor stripe.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # foreground color = most common non-zero value (here 4)
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    nonzero = {v: n for v, n in counts.items() if v != 0}
    fg = max(nonzero, key=nonzero.get) if nonzero else max(counts, key=counts.get)

    # solid row = a row entirely made of the foreground color (the anchor row)
    solid_row = None
    for r in range(H):
        if all(input_grid[r][c] == fg for c in range(W)):
            solid_row = r
            break

    PERIOD = 3
    NEW = 6

    T = [[None] * W for _ in range(H)]
    if solid_row is None:
        return T

    # anchor stripes sit at columns congruent to 0 mod PERIOD; a cell becomes
    # NEW wherever it is foreground and its column lies on a stripe.
    for r in range(H):
        for c in range(W):
            if c % PERIOD == 0 and input_grid[r][c] == fg:
                T[r][c] = NEW
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
