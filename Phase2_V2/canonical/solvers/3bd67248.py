def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure: a marker column lives at column 0 (single solid color), the
    rest of the grid is background. We draw:
      - an anti-diagonal of 2s from the top-right corner down toward the
        marker column (cell (r, W-1-r) for every interior row), and
      - a baseline of 4s along the bottom row (excluding the marker column).
    The marker column (column 0) is never touched.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r in range(H):
        for c in range(W):
            if c == 0:
                continue  # preserve the marker column
            if r == H - 1:
                T[(r, c)] = 4          # bottom baseline
            elif c == W - 1 - r:
                T[(r, c)] = 2          # anti-diagonal
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
