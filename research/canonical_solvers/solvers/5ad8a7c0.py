"""Canonical solver for ARC puzzle 5ad8a7c0.

Rule
----
The grid contains a single foreground color whose cells form concentric,
mirror-symmetric "rings": each ring shows up as a row holding exactly two
foreground cells located at mirror columns (k, W-1-k).  Different rows can sit
at different rings, identified by the ring index k = the smaller column.

Only the *innermost* ring present (largest k, i.e. the dots closest to the
vertical center axis) gets its horizontal gap closed: every cell strictly
between the two dots of those rows is painted with the foreground color.  All
outer rings keep their isolated dots.  When the innermost ring is the central
adjacent pair there is no gap, so nothing changes.

infer_T computes the latent mask of cells to paint; apply_T copies the input
and overwrites only the masked cells.
"""


def _foreground_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None
    bg = max(counts, key=counts.get)
    fg = [v for v in counts if v != bg]
    if not fg:
        return None
    # the lone non-background color
    return max(fg, key=counts.get)


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    T = [[None] * W for _ in range(H)]

    fg = _foreground_color(input_grid)
    if fg is None:
        return T

    # Collect mirror-symmetric dot rows grouped by ring index k = min column.
    rings = {}
    for r in range(H):
        cols = [c for c in range(W) if input_grid[r][c] == fg]
        if len(cols) == 2 and cols[0] + cols[1] == W - 1:
            rings.setdefault(cols[0], []).append((r, cols[0], cols[1]))

    if not rings:
        return T

    inner = max(rings)  # innermost ring = largest min-column
    for r, c0, c1 in rings[inner]:
        for c in range(c0 + 1, c1):
            T[r][c] = fg
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
