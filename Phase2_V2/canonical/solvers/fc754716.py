def infer_T(input_grid):
    """Infer a latent mask: paint the grid's border with the unique marker color.

    The input contains a single non-background marker pixel. The transformation
    draws a one-cell-thick frame around the whole grid in that marker's color.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # marker color = the unique non-background value
    marker = next((v for v in counts if v != bg), bg)
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if r == 0 or r == H - 1 or c == 0 or c == W - 1:
                T[r][c] = marker
            elif input_grid[r][c] == marker:
                # erase the interior marker pixel back to background
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
