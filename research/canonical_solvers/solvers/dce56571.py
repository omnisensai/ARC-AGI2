"""Canonical solver for ARC task dce56571.

Rule: A scattered shape of N non-background cells (single foreground color) is
"collapsed" into a single horizontal bar of length N drawn in the grid's
center: the bar occupies the middle row and is horizontally centered. The bar
is painted in the shape's color; everything else becomes background.

Canonical latent-T form:
  - infer_T scans the input for the background color (most common) and the
    foreground cells, then builds a mask grid where the centered horizontal bar
    cells are assigned the foreground color and every other previously-colored
    cell is cleared back to background.
  - apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    bg = _background(input_grid)

    # Foreground cells (the scattered shape) and its color.
    fg_cells = [(r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] != bg]

    # Latent mask: None = leave cell untouched.
    T = [[None] * W for _ in range(H)]

    if not fg_cells:
        return T

    color = input_grid[fg_cells[0][0]][fg_cells[0][1]]
    N = len(fg_cells)

    # Bar geometry: middle row, horizontally centered, length N.
    bar_row = (H - 1) // 2
    left = (W - N) // 2

    # Clear the original scattered cells.
    for (r, c) in fg_cells:
        T[r][c] = bg

    # Draw the centered horizontal bar (overrides any cleared cells it covers).
    for c in range(left, left + N):
        if 0 <= c < W:
            T[bar_row][c] = color

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
