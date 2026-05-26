def infer_T(input_grid):
    """Infer the latent transformation mask: an L-shaped connector (color 4)
    from the 8-marker to the 2-marker. The path runs vertically along the 8's
    column to the 2's row, then horizontally along the 2's row to the 2. The
    corner sits at (2's row, 8's column). Endpoints (8 and 2) are not painted."""
    H, W = len(input_grid), len(input_grid[0])
    pos = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (2, 8):
                pos[v] = (r, c)
    T = {}
    if 2 not in pos or 8 not in pos:
        return T
    r8, c8 = pos[8]
    r2, c2 = pos[2]

    cells = set()
    # Vertical segment along the 8's column, from r8 to r2 (corner at (r2, c8)).
    step = 1 if r2 >= r8 else -1
    for r in range(r8, r2 + step, step):
        cells.add((r, c8))
    # Horizontal segment along the 2's row, from c8 to c2.
    step = 1 if c2 >= c8 else -1
    for c in range(c8, c2 + step, step):
        cells.add((r2, c))

    for (r, c) in cells:
        if (r, c) == (r8, c8) or (r, c) == (r2, c2):
            continue  # leave the markers intact
        T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
