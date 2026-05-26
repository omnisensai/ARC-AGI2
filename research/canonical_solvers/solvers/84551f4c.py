def _bars(grid):
    """Find vertical bars (single-column nonzero runs): (col, color, height)."""
    H = len(grid)
    W = len(grid[0]) if H else 0
    bars = []
    for c in range(W):
        col = [grid[r][c] for r in range(H)]
        nz = [v for v in col if v != 0]
        if nz:
            bars.append((c, nz[0], len(nz)))
    return bars


def infer_T(input_grid):
    """Latent mask: dict {(r,c): new_color} of cells to overwrite.

    The grid holds width-1 vertical bars. Bars topple to the right like
    dominoes onto the bottom row. A color-1 bar is a group leader and always
    falls. A bar falls if the previous bar fell and the gap to it is <= that
    previous bar's height (it gets knocked over); otherwise it stays standing.
    A fallen bar becomes a horizontal segment of its color, length = its
    height, starting at its own column. Standing bars are kept; everything
    else is cleared.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    bars = _bars(input_grid)

    # Determine which bars fall (domino propagation, left to right).
    fall = {}
    prev = None  # (col, color, height) of previously seen bar
    for (c, color, h) in bars:
        if color == 1:            # group leader always topples
            fall[c] = True
        elif prev is None:
            fall[c] = True
        else:
            pc, _pcol, ph = prev
            gap = c - pc
            fall[c] = fall.get(pc, False) and gap <= ph
        prev = (c, color, h)

    standing_cols = {c for (c, color, h) in bars if not fall[c]}

    # Build the mask. Start by clearing every originally-nonzero cell, then
    # repaint: standing bars stay put; fallen bars become horizontal runs on
    # the bottom row.
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                T[(r, c)] = 0

    bottom = H - 1
    for (c, color, h) in bars:
        if c in standing_cols:
            # keep standing bar exactly as-is (undo the clear)
            for r in range(H):
                if input_grid[r][c] != 0:
                    T[(r, c)] = input_grid[r][c]
        else:
            for k in range(h):
                cc = c + k
                if 0 <= cc < W:
                    T[(bottom, cc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
