def infer_T(input_grid):
    """Infer the latent fill mask.

    Structure: the top row holds 'column markers' (cells == 5) and the last
    column holds 'row markers' (cells == 5). For every marked row, the pattern
    of marked columns is stamped with color 2 (skipping the original markers).
    """
    H, W = len(input_grid), len(input_grid[0])

    # Columns marked by a 5 in the top row.
    marker_cols = [c for c in range(W) if input_grid[0][c] == 5]

    # Rows marked by a 5 in the last column.
    marker_rows = [r for r in range(H) if input_grid[r][W - 1] == 5]

    T = {}
    for r in marker_rows:
        for c in marker_cols:
            if input_grid[r][c] != 5:
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
