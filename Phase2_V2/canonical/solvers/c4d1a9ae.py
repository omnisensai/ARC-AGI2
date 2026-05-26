"""Canonical solver for ARC puzzle c4d1a9ae.

Structure: the grid is divided into vertical panels by uniform separator
columns (columns whose cells are all the same color). The most common color
overall is the background. Each panel contains the background plus exactly one
foreground color. Rule: within each panel, every background cell is recolored
to the foreground color of the NEXT panel (cyclically); foreground cells and
separator columns are left unchanged.
"""

from collections import Counter


def _background(grid):
    c = Counter()
    for row in grid:
        for v in row:
            c[v] += 1
    return c.most_common(1)[0][0]


def _panels(grid):
    """Return list of column-groups separated by uniform columns."""
    H, W = len(grid), len(grid[0])
    sep = set(
        c for c in range(W)
        if len(set(grid[r][c] for r in range(H))) == 1
    )
    groups, cur = [], []
    for c in range(W):
        if c in sep:
            if cur:
                groups.append(cur)
                cur = []
        else:
            cur.append(c)
    if cur:
        groups.append(cur)
    return groups


def _panel_foreground(grid, cols, bg):
    """The single non-background color appearing in a panel's columns."""
    H = len(grid)
    fg = None
    for r in range(H):
        for c in cols:
            v = grid[r][c]
            if v != bg:
                fg = v
    return fg


def infer_T(input_grid):
    """Infer the latent transformation mask: {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    groups = _panels(input_grid)

    fgs = [_panel_foreground(input_grid, g, bg) for g in groups]

    T = {}
    n = len(groups)
    for i, cols in enumerate(groups):
        next_fg = fgs[(i + 1) % n] if n else None
        if next_fg is None:
            continue
        for r in range(H):
            for c in cols:
                if input_grid[r][c] == bg:
                    T[(r, c)] = next_fg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
