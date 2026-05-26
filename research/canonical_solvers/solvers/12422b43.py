def infer_T(input_grid):
    """Infer the latent overwrite mask T as {(r,c): color}.

    Structure: column 0 holds a vertical run of `k` 5-markers. A non-zero
    'pattern' occupies the top rows (cols >= 1). The first `k` pattern rows
    form a seed that is tiled downward (cols >= 1 only) starting just below the
    last pattern row, filling the remaining grid.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # k = number of 5 markers in column 0
    k = sum(1 for r in range(H) if input_grid[r][0] == 5)

    # rows that contain any non-zero content in cols >= 1 (the pattern)
    pat_rows = [r for r in range(H)
                if any(input_grid[r][c] != 0 for c in range(1, W))]

    T = {}
    if k <= 0 or not pat_rows:
        return T

    pat_end = max(pat_rows)

    # seed = first k pattern rows (cols >= 1 only)
    seed = []
    for r in range(k):
        seed.append([input_grid[r][c] for c in range(W)])

    # tile the seed downward starting just after the pattern
    start = pat_end + 1
    for i, r in enumerate(range(start, H)):
        srow = seed[i % k]
        for c in range(1, W):
            T[(r, c)] = srow[c]

    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
