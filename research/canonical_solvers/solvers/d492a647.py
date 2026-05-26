def infer_T(input_grid):
    """Infer a latent transformation mask.

    The grid contains a noisy field of 0 (empty) and 5 (wall), plus exactly one
    single 'marker' cell of some other color sitting inside a rectangular region
    of empty cells. The marker defines a parity lattice: every cell sharing the
    marker's row-parity AND column-parity is part of the lattice. Wherever such a
    lattice cell is empty (0), it gets stamped with the marker color; wall cells
    (5) are left untouched. The result is a regular grid of dots seeded from the
    marker.

    Returns a dict {(r, c): new_color} of cells to overwrite.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Locate the single marker cell (any color other than 0/empty or 5/wall).
    marker = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v != 5:
                marker = (r, c, v)
                break
        if marker is not None:
            break

    T = {}
    if marker is None:
        return T

    mr, mc, color = marker
    for r in range(H):
        for c in range(W):
            if (r - mr) % 2 == 0 and (c - mc) % 2 == 0 and input_grid[r][c] == 0:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
