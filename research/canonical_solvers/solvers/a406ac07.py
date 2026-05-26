def infer_T(input_grid):
    """Latent mask: for each header color, fill the rectangle that is the
    intersection of the rows where the right-column header equals that color
    and the columns where the bottom-row header equals that color."""
    H, W = len(input_grid), len(input_grid[0])
    col_header = [input_grid[r][W - 1] for r in range(H - 1)]  # right column (per row)
    row_header = [input_grid[H - 1][c] for c in range(W - 1)]  # bottom row (per col)
    colors = set(col_header) | set(row_header)
    T = {}
    for color in colors:
        rows = [r for r in range(H - 1) if col_header[r] == color]
        cols = [c for c in range(W - 1) if row_header[c] == color]
        for r in rows:
            for c in cols:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
