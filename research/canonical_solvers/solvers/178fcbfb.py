def infer_T(input_grid):
    """Infer the latent overwrite mask from marker cells.

    Each non-background marker extends into a full line:
      - color 2 -> a vertical line filling its entire column
      - colors 1 and 3 -> a horizontal line filling their entire row
    Horizontal (row) lines are painted after the vertical lines, so where
    they cross, the row line wins.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]

    # Color 2 markers -> vertical column lines.
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                for rr in range(H):
                    T[rr][c] = 2

    # Colors 1 and 3 markers -> horizontal row lines (override verticals).
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (1, 3):
                for cc in range(W):
                    T[r][cc] = v

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
