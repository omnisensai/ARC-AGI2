"""Canonical ARC solver for puzzle e21d9049.

Rule: the input contains a single cross/plus marker -- a center cell with a
horizontal arm (consecutive nonzero cells in its row) and a vertical arm
(consecutive nonzero cells in its column). Each arm encodes one full period of
a color cycle. The transformation tiles the horizontal arm's color sequence
across the entire center row and the vertical arm's sequence down the entire
center column, keeping the tiling aligned with the arm's original position.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_center(grid, bg):
    H, W = len(grid), len(grid[0])
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg:
                continue
            hor = (c - 1 >= 0 and grid[r][c - 1] != bg) or \
                  (c + 1 < W and grid[r][c + 1] != bg)
            ver = (r - 1 >= 0 and grid[r - 1][c] != bg) or \
                  (r + 1 < H and grid[r + 1][c] != bg)
            if hor and ver:
                return (r, c)
    return None


def infer_T(input_grid):
    """Infer the latent transformation mask {(r, c): new_color}.

    Locates the cross marker, reads the period sequences from its arms, and
    computes the tiled color for every cell of the center row and column.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    center = _find_center(input_grid, bg)
    T = {}
    if center is None:
        return T
    cr, cc = center

    # Horizontal arm: consecutive nonzero cells in the center row.
    cols = [c for c in range(W) if input_grid[cr][c] != bg]
    c0, c1 = min(cols), max(cols)
    row_seq = [input_grid[cr][c] for c in range(c0, c1 + 1)]
    P = len(row_seq)

    # Vertical arm: consecutive nonzero cells in the center column.
    rows = [r for r in range(H) if input_grid[r][cc] != bg]
    r0, r1 = min(rows), max(rows)
    col_seq = [input_grid[r][cc] for r in range(r0, r1 + 1)]
    Q = len(col_seq)

    # Tile the horizontal sequence across the whole center row.
    for c in range(W):
        T[(cr, c)] = row_seq[(c - c0) % P]

    # Tile the vertical sequence down the whole center column.
    for r in range(H):
        T[(r, cc)] = col_seq[(r - r0) % Q]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
