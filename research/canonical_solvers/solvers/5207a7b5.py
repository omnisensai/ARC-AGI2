def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Locate the vertical line of 5s: its column and length (anchored at row 0).
    cells5 = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    T = {}
    if not cells5:
        return T
    c = cells5[0][1]
    L = len(cells5)
    # Left of the line: column at distance d gets an 8-staircase of height L + 2*d.
    for d in range(1, c + 1):
        col = c - d
        h = L + 2 * d
        for r in range(min(h, H)):
            T[(r, col)] = 8
    # Right of the line: column at distance d gets a 6-staircase of height L - 2*d.
    for d in range(1, W - c):
        col = c + d
        h = L - 2 * d
        for r in range(min(max(h, 0), H)):
            T[(r, col)] = 6
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
