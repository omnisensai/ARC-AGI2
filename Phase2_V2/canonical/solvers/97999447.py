def infer_T(input_grid):
    """For each non-background (non-zero) seed pixel, build a mask that extends
    its row rightward to the grid edge, alternating the seed's color and 5
    (5, then seed color repeating), starting with the seed color at the seed's
    own column."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                for cc in range(c, W):
                    T[(r, cc)] = v if (cc - c) % 2 == 0 else 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
