def infer_T(input_grid):
    """Per-column rule: each vertical bar of 2s rises to stack immediately
    below the top contiguous run of 1s in its column, preserving its length.
    Returns a latent mask {(r,c): new_color} of changed cells."""
    H = len(input_grid)
    W = len(input_grid[0])
    T = {}
    for c in range(W):
        col = [input_grid[r][c] for r in range(H)]
        k = sum(1 for v in col if v == 2)
        if k == 0:
            continue
        # length of the top contiguous run of 1s in this column
        L = 0
        while L < H and col[L] == 1:
            L += 1
        # clear the original 2 cells in this column
        for r in range(H):
            if col[r] == 2:
                T[(r, c)] = 0
        # place k twos starting right below the top 1-run
        for j in range(k):
            r = L + j
            if 0 <= r < H:
                T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
