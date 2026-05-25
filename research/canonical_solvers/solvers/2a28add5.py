def infer_T(input_grid):
    """Build a latent mask {(r,c): 8} of cells to paint.

    Background is the most frequent color (7 in this task). For every cell
    holding the marker color 6, count the non-background cells lying to its
    left and to its right within the same row. The 6 emits a horizontal run
    of 8s spanning from (col - left_count) to (col + right_count).
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    marker = 6

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != marker:
                continue
            left = sum(1 for cc in range(0, c) if input_grid[r][cc] != bg)
            right = sum(1 for cc in range(c + 1, W) if input_grid[r][cc] != bg)
            lo = max(0, c - left)
            hi = min(W - 1, c + right)
            for cc in range(lo, hi + 1):
                T[(r, cc)] = 8
    return T, bg


def apply_T(input_grid, T):
    """Background-fill the grid, then overwrite masked cells with their color."""
    mask, bg = T
    H, W = len(input_grid), len(input_grid[0])
    out = [[bg] * W for _ in range(H)]
    for (r, c), color in mask.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
