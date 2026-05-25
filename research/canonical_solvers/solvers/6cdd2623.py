from collections import Counter


def infer_T(input_grid):
    """Latent mask. The rarest nonzero color is the 'line' color; its cells sit
    on the grid edges as endpoint markers. A left-edge + right-edge marker on the
    same row defines a full row line; a top-edge + bottom-edge marker on the same
    column defines a full column line. The mask makes every cell explicit: the
    line color along those rows/cols, 0 everywhere else (all other noise cleared).
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    counts.pop(0, None)
    T = [[0] * W for _ in range(H)]
    if not counts:
        return T
    sp = min(counts, key=lambda k: counts[k])
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == sp]
    rows_left = {r for (r, c) in cells if c == 0}
    rows_right = {r for (r, c) in cells if c == W - 1}
    cols_top = {c for (r, c) in cells if r == 0}
    cols_bot = {c for (r, c) in cells if r == H - 1}
    for r in (rows_left & rows_right):
        for c in range(W):
            T[r][c] = sp
    for c in (cols_top & cols_bot):
        for r in range(H):
            T[r][c] = sp
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
