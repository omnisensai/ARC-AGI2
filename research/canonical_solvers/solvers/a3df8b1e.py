def infer_T(input_grid):
    """Trace a 45-degree ray bouncing off the side walls, starting from the
    single marker cell on the bottom row and travelling upward. Returns a
    latent mask {(r, c): color} of every cell the ray passes through."""
    H, W = len(input_grid), len(input_grid[0])
    start = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                start = (r, c)
    T = {}
    if start is None:
        return T
    r, c = start
    color = input_grid[r][c]
    dc = 1  # initial horizontal step (toward the right wall)
    while 0 <= r < H:
        T[(r, c)] = color
        nr = r - 1            # always move up one row
        nc = c + dc           # step horizontally
        if nc < 0:            # bounce off left wall
            dc = 1
            nc = c + dc
        elif nc > W - 1:      # bounce off right wall
            dc = -1
            nc = c + dc
        r, c = nr, nc
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
