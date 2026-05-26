def infer_T(input_grid):
    """Infer a latent transformation mask: for each row, find the column of the
    single marker cell (5) and map that column position to an output color.
    Mapping: col 0 -> 2 (left), col 1 -> 4 (center), col 2 -> 3 (right)."""
    H, W = len(input_grid), len(input_grid[0])
    # background = most frequent color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # marker color = the non-background color present
    markers = [v for v in counts if v != bg]
    marker = markers[0] if markers else None

    col_to_color = {0: 2, 1: 4, 2: 3}
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        marker_col = next((c for c in range(W) if input_grid[r][c] == marker), None)
        if marker_col is None:
            continue
        color = col_to_color.get(marker_col)
        if color is None:
            continue
        for c in range(W):
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
