"""Canonical solver for ARC task d06dbe63.

Rule: a single 8 marker emits a staircase of color-5 cells in two opposite
diagonal directions. Going up the staircase steps to the right; going down it
steps to the left. Each step is: one vertical cell, then a horizontal bar of
three cells anchored at the current column extending in the step direction,
then the anchor advances to the far end of that bar. Cells outside the grid are
simply not drawn.
"""


def _staircase(start, dr, dc, H, W):
    """Yield (r, c) cells of one staircase arm from the marker `start`.

    dr: vertical step direction (-1 up, +1 down)
    dc: horizontal extension direction (+1 right, -1 left)
    """
    r0, c0 = start
    r, c = r0, c0
    cells = []
    # Loop while the vertical anchor row could still be on the grid.
    while True:
        r += dr
        if not (0 <= r < H):
            break
        # vertical cell at current anchor column
        if 0 <= c < W:
            cells.append((r, c))
        r += dr
        if not (0 <= r < H):
            break
        # horizontal bar of 3 from anchor column extending dc
        for k in range(3):
            cc = c + dc * k
            if 0 <= cc < W:
                cells.append((r, cc))
        c += dc * 2
        # safety: stop if anchor column has run far off-grid in the dc direction
        if dc > 0 and c >= W:
            break
        if dc < 0 and c < 0:
            break
    return cells


def infer_T(input_grid):
    """Compute the latent transformation mask: {(r, c): new_color}."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 8:
                marker = (r, c)
                break
        if marker is not None:
            break
    T = {}
    if marker is None:
        return T
    # Upward arm steps right; downward arm steps left.
    for (r, c) in _staircase(marker, -1, +1, H, W):
        T[(r, c)] = 5
    for (r, c) in _staircase(marker, +1, -1, H, W):
        T[(r, c)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
