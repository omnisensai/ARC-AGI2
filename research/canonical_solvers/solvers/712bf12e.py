def infer_T(input_grid):
    """Trace a ray upward from each marker (2) on the bottom; the ray climbs
    the column until the cell above is a 5 obstacle, then steps one cell to the
    right and resumes climbing. If both up and right are blocked the ray stops.
    Returns a latent mask {(r,c): 2} of all cells the rays pass through."""
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == 2]
    T = {}
    for (mr, mc) in markers:
        r, c = mr, mc
        T[(r, c)] = 2
        while True:
            if r - 1 < 0:
                break  # reached the top edge
            if input_grid[r - 1][c] != 5:
                r -= 1                       # climb up
                T[(r, c)] = 2
            elif c + 1 < W and input_grid[r][c + 1] != 5:
                c += 1                       # obstacle above: step right
                T[(r, c)] = 2
            else:
                break                        # blocked up and right: stop
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
