def infer_T(input_grid):
    """Latent mask: for each column, swap rows in consecutive pairs starting
    from the ends; the exact middle row of an odd-height column stays fixed.
    Only cells whose value changes are recorded in the mask."""
    H = len(input_grid)
    W = len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    # Order in which rows are paired; for odd H, drop the center so it is fixed.
    idxs = list(range(H))
    if H % 2 == 1:
        mid = H // 2
        idxs = [r for r in range(H) if r != mid]
    for c in range(W):
        col = [input_grid[r][c] for r in range(H)]
        target = col[:]
        for k in range(0, len(idxs) - 1, 2):
            a, b = idxs[k], idxs[k + 1]
            target[a], target[b] = col[b], col[a]
        for r in range(H):
            if target[r] != col[r]:
                T[r][c] = target[r]
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
