def infer_T(input_grid):
    """Build a latent mask {(r,c): new_color}.

    Rule: every column that has a non-background (5) marker in the bottom row
    is an "active" column. Within such a column, the scattered colored markers
    (top->bottom) partition the column into bands: each marker at row r with
    color v fills every cell from just below the previous marker's row down to
    and including its own row r. The bottom 5 marker fills the lowest band.
    """
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    T = {}
    for c in range(W):
        if input_grid[H - 1][c] == 0:
            continue  # column not activated by a bottom-row marker
        markers = [(r, input_grid[r][c]) for r in range(H) if input_grid[r][c] != 0]
        prev = -1
        for (r, v) in markers:
            for rr in range(prev + 1, r + 1):
                T[(rr, c)] = v
            prev = r
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
