def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    T = {}
    if len(markers) != 2:
        return T
    rs = sorted(set(r for r, c in markers))
    cs = sorted(set(c for r, c in markers))
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    # full grid-spanning lines (color 2) through each marker's row and column
    line_rows = {r for r, c in markers}
    line_cols = {c for r, c in markers}
    for r in range(H):
        for c in range(W):
            if r in line_rows or c in line_cols:
                T[(r, c)] = 2
    # interior of the rectangle (strictly between the two rows/cols) filled with 1
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
