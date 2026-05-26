# Canonical solver for ARC puzzle 6ea4a07e
#
# Rule: the input contains a single non-zero "source" color over a 0 background.
# The output is the figure/ground inversion: every 0 cell is filled with a color
# determined by the source color, and every source-colored cell becomes 0.
# Source -> fill mapping observed across all pairs: 5->4, 8->2, 3->1.

COLOR_MAP = {5: 4, 8: 2, 3: 1}


def infer_T(input_grid):
    """Infer the latent transformation mask from the input alone.

    T[r][c] is the color each cell should become: the mapped fill color for
    background (0) cells, and 0 for the source-colored cells.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Identify the single non-zero source color present in the grid.
    src = None
    for row in input_grid:
        for v in row:
            if v != 0:
                src = v
                break
        if src is not None:
            break

    out_color = COLOR_MAP.get(src) if src is not None else None

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[r][c] = out_color
            else:
                T[r][c] = 0
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
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
