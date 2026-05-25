def infer_T(input_grid):
    """Latent mask: recolor every 0 by the rank of its column.

    The grid contains scattered 0 markers. Exactly the columns that hold at
    least one 0 are relevant; ordered left-to-right they receive colors
    1, 2, 3, 4. Every 0 in a given column is mapped to that column's color.
    """
    H = len(input_grid)
    W = len(input_grid[0])
    cols_with_zero = [c for c in range(W)
                      if any(input_grid[r][c] == 0 for r in range(H))]
    cols_with_zero.sort()
    col_color = {c: i + 1 for i, c in enumerate(cols_with_zero)}
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0 and c in col_color:
                T[(r, c)] = col_color[c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
