def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # pattern width k = number of leading columns before the first all-zero column
    k = W
    for c in range(W):
        if all(input_grid[r][c] == 0 for r in range(H)):
            k = c
            break
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        edge = input_grid[r][0]            # outer border color for this row
        for c in range(k, W):
            if c >= W - k:                 # right border: mirror-copy the pattern block
                T[r][c] = input_grid[r][c - (W - k)]
            else:                          # interior fill with the row's edge color
                T[r][c] = edge
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
