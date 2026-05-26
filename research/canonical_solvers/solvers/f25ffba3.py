def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Most common color = background / blank.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The content occupies a contiguous block at one vertical end; the rest is blank.
    # The latent transformation makes the grid symmetric across the horizontal midline:
    # each blank cell is filled from its vertically mirrored counterpart when that cell
    # holds content. This reflects the existing content into the empty half.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        mirror = H - 1 - r
        for c in range(W):
            if input_grid[r][c] == bg and input_grid[mirror][c] != bg:
                T[r][c] = input_grid[mirror][c]
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
