def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    marker = next(((r, c, input_grid[r][c]) for r in range(H) for c in range(W)
                   if input_grid[r][c] != 0), None)
    T = {}
    if marker is None:
        return T
    mr, mc, mcol = marker
    # Fill the band of rows 0..mr at columns matching marker-column parity with 4.
    for r in range(0, mr + 1):
        for c in range(W):
            if c % 2 == mc % 2:
                T[(r, c)] = 4
    # Move the marker down by one row (its color), overwriting the stripe there.
    T[(mr + 1, mc)] = mcol
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
