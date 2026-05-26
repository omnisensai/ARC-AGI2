def infer_T(input_grid):
    """Infer the latent change mask.

    For each row that has two distinct non-background endpoints (a colored cell
    on the left and one on the right), draw a line between them: the left color
    fills from the left endpoint up to (but not including) the midpoint, the
    midpoint cell becomes 5, and the right color fills the rest to the right
    endpoint.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}
    for r in range(H):
        left_c = next((c for c in range(W) if input_grid[r][c] != bg), None)
        right_c = next((c for c in range(W - 1, -1, -1) if input_grid[r][c] != bg), None)
        if left_c is None or right_c is None or left_c == right_c:
            continue
        lcol = input_grid[r][left_c]
        rcol = input_grid[r][right_c]
        mid = (left_c + right_c) // 2
        for c in range(left_c, right_c + 1):
            if c < mid:
                T[(r, c)] = lcol
            elif c == mid:
                T[(r, c)] = 5
            else:
                T[(r, c)] = rcol
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
