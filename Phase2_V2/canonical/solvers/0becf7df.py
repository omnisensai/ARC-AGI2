def infer_T(input_grid):
    """Read the 2x2 legend at the top-left corner. Each ROW of the legend is a
    color-swap pair. Build a mask that recolors every non-legend cell whose
    color appears in a swap pair to its partner color."""
    H, W = len(input_grid), len(input_grid[0])
    a, b = input_grid[0][0], input_grid[0][1]
    c, d = input_grid[1][0], input_grid[1][1]
    swap = {a: b, b: a, c: d, d: c}
    legend_cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    T = {}
    for r in range(H):
        for col in range(W):
            if (r, col) in legend_cells:
                continue
            v = input_grid[r][col]
            if v in swap:
                T[(r, col)] = swap[v]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
