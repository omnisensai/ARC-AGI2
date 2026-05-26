def infer_T(input_grid):
    """Infer a latent mask: below a separator row, fill each row with a color
    cycling through the header (row 0) palette in order."""
    H = len(input_grid)
    W = len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    if H < 3:
        return T
    header = input_grid[0]
    # Identify separator row: a row entirely of one constant color (other than
    # the header), located at row 1 — the boundary between header and fill zone.
    sep_row = None
    for r in range(1, H):
        row = input_grid[r]
        if len(set(row)) == 1:
            sep_row = r
            break
    if sep_row is None:
        return T
    palette = list(header)
    n = len(palette)
    if n == 0:
        return T
    # Fill rows after the separator, cycling through the header palette.
    for r in range(sep_row + 1, H):
        idx = (r - (sep_row + 1)) % n
        color = palette[idx]
        for c in range(W):
            T[r][c] = color
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
