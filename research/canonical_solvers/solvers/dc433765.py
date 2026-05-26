"""Canonical latent-T solver for ARC puzzle dc433765.

Rule: the grid contains exactly two non-background marker cells, one of color 3
(the mover) and one of color 4 (the anchor). The 3-cell takes a single step
toward the 4-cell: it advances one cell along each axis in the direction of the
4-cell (using the sign of the coordinate difference; no movement along an axis
where the two are already aligned). The mover's old position is cleared to the
background color and its new position is painted 3. The 4-cell never moves.

infer_T builds a latent mask {(r,c): new_color} describing exactly the cells that
change; apply_T copies the input and overwrites only those masked cells.
"""


def _sign(d):
    return (d > 0) - (d < 0)


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Background = most frequent color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get) if counts else 0

    mover = None    # cell of color 3
    anchor = None   # cell of color 4
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 3:
                mover = (r, c)
            elif v == 4:
                anchor = (r, c)

    T = {}
    if mover is None or anchor is None:
        return T

    mr, mc = mover
    ar, ac = anchor

    # Single step toward the anchor along each axis.
    nr = mr + _sign(ar - mr)
    nc = mc + _sign(ac - mc)

    if (nr, nc) == (mr, mc):
        return T  # nowhere to move

    # Clear old position, paint new position.
    T[(mr, mc)] = bg
    T[(nr, nc)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
