def infer_T(input_grid):
    """Latent mask: dict {(r,c): new_color}.

    The grid is divided into 3x3 cells by all-zero separator rows/cols.
    Within each cell the pattern is inverted: 8 -> 0 and 0 -> 2.
    Separator cells (any cell on an all-zero row or all-zero column) are
    left untouched.
    """
    H, W = len(input_grid), len(input_grid[0])
    sep_rows = set(r for r in range(H) if all(v == 0 for v in input_grid[r]))
    sep_cols = set(c for c in range(W)
                   if all(input_grid[r][c] == 0 for r in range(H)))
    T = {}
    for r in range(H):
        for c in range(W):
            if r in sep_rows or c in sep_cols:
                continue
            if input_grid[r][c] == 0:
                T[(r, c)] = 2
            else:
                T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
