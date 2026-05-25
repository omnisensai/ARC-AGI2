def infer_T(input_grid):
    """Each nonzero cell in row 0 is a marker of color v at column c.
    It radiates a vertical zigzag down the grid: on even rows the marker
    column is painted, on odd rows the two flanking columns are painted."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    markers = [(c, input_grid[0][c]) for c in range(W) if input_grid[0][c] != 0]
    for c, v in markers:
        for r in range(H):
            cols = [c] if r % 2 == 0 else [c - 1, c + 1]
            for cc in cols:
                if 0 <= cc < W:
                    T[(r, cc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
