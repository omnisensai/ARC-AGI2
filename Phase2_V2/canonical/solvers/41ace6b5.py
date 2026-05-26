def infer_T(input_grid):
    """Infer a latent mask {(r,c): new_color} for puzzle 41ace6b5.

    Structure: even columns are 'anchor' columns holding a 2-row and the 5-row
    directly below it; they never change.  Odd columns are vertical strips made
    of a contiguous 8-block on top of a 1-block (over a field of 7s).

    Rule (per odd column): normalize every strip so its 8-block has the maximum
    8-height found across all strips (M8), with the 8-block sitting in the M8
    rows immediately above the 5-row, the 1-block (its own height preserved)
    starting at the 5-row, and everything below the 1-block becoming 9.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # locate the 5-row: the row whose first cell is a 5 (anchor row).
    r5 = None
    for r in range(H):
        if input_grid[r][0] == 5:
            r5 = r
            break
    if r5 is None:
        return {}

    odd_cols = list(range(1, W, 2))

    # M8 = max count of 8s among the odd (strip) columns.
    M8 = 0
    for c in odd_cols:
        n8 = sum(1 for r in range(H) if input_grid[r][c] == 8)
        if n8 > M8:
            M8 = n8
    if M8 == 0:
        return {}

    T = {}
    top8 = r5 - M8  # first row of the normalized 8-block
    for c in odd_cols:
        # preserve this strip's own 1-count.
        n1 = sum(1 for r in range(H) if input_grid[r][c] == 1)
        for r in range(H):
            if r < top8:
                new = 7
            elif r < r5:                 # 8-block region: [top8, r5)
                new = 8
            elif r < r5 + n1:            # 1-block region: [r5, r5+n1)
                new = 1
            else:                        # below the 1-block
                new = 9
            if input_grid[r][c] != new:
                T[(r, c)] = new
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
