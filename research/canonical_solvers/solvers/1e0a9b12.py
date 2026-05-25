def infer_T(input_grid):
    """Latent mask: gravity pulls every non-background cell down within its
    column, stacking them (in top-to-bottom order) at the column's bottom."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    T = [[None] * W for _ in range(H)]
    for c in range(W):
        vals = [input_grid[r][c] for r in range(H) if input_grid[r][c] != bg]
        n = len(vals)
        for r in range(H):
            if r >= H - n:
                T[r][c] = vals[r - (H - n)]
            else:
                T[r][c] = bg
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
