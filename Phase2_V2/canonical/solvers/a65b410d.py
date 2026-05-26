def infer_T(input_grid):
    """Find the horizontal bar of 2s (left-aligned). Build a mask that, for each
    row above the bar at distance k, paints color 3 over length L+k cells, and for
    each row below at distance k, paints color 1 over length L-k cells (left-aligned).
    L is the bar length. Cells with length<=0 are not painted."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1

    # locate the bar of 2s: a contiguous left-aligned run on a single row
    bar_row = None
    L = 0
    for r in range(H):
        run = 0
        for c in range(W):
            if input_grid[r][c] == 2:
                run += 1
            else:
                break
        if run > 0:
            bar_row, L = r, run
            break

    T = [[None] * W for _ in range(H)]
    if bar_row is None or L == 0:
        return T

    for r in range(H):
        if r == bar_row:
            continue
        if r < bar_row:
            k = bar_row - r
            length = L + k
            color = 3
        else:
            k = r - bar_row
            length = L - k
            color = 1
        for c in range(length):
            if 0 <= c < W:
                T[r][c] = color
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
