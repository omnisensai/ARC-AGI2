def infer_T(input_grid):
    """Find the two 2-markers and trace the straight line between them.
    Latent mask T maps each cell on the line to its new color:
    a 0 becomes 2 (background of the line) and a 1 becomes 3."""
    H, W = len(input_grid), len(input_grid[0])
    pts = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    T = {}
    if len(pts) != 2:
        return T
    (r0, c0), (r1, c1) = pts
    dr = (r1 > r0) - (r1 < r0)
    dc = (c1 > c0) - (c1 < c0)
    r, c = r0, c0
    while True:
        v = input_grid[r][c]
        if v == 1:
            T[(r, c)] = 3
        else:
            T[(r, c)] = 2
        if (r, c) == (r1, c1):
            break
        r += dr
        c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
