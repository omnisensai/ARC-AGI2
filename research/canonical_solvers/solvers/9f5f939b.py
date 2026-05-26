def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} marking the centers of the
    cross-of-dominoes configuration.

    The grid is dotted with length-2 dominoes (two adjacent 1s) on an 8
    background.  Where four dominoes point inward at a common empty cell --
    a vertical domino above (rows r-3,r-2), a vertical domino below
    (rows r+2,r+3), a horizontal domino left (cols c-3,c-2) and a horizontal
    domino right (cols c+2,c+3) -- the empty center cell is filled with 4.
    """
    H, W = len(input_grid), len(input_grid[0])

    def is_one(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] == 1

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 8:
                continue
            if (is_one(r - 3, c) and is_one(r - 2, c) and
                    is_one(r + 2, c) and is_one(r + 3, c) and
                    is_one(r, c - 3) and is_one(r, c - 2) and
                    is_one(r, c + 2) and is_one(r, c + 3)):
                T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
