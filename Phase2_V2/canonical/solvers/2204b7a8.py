def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    marker = 3

    # Detect two parallel "wall" lines: either full top/bottom rows or full
    # left/right columns, each a uniform non-zero, non-marker color.
    def uniform_row(r):
        vals = set(input_grid[r])
        if len(vals) == 1:
            v = next(iter(vals))
            if v != 0 and v != marker:
                return v
        return None

    def uniform_col(c):
        vals = {input_grid[r][c] for r in range(H)}
        if len(vals) == 1:
            v = next(iter(vals))
            if v != 0 and v != marker:
                return v
        return None

    top = uniform_row(0)
    bottom = uniform_row(H - 1)
    left = uniform_col(0)
    right = uniform_col(W - 1)

    # Determine orientation and (low-index color, high-index color, axis).
    if top is not None and bottom is not None:
        axis = 'row'
        low_color, high_color = top, bottom
        low_idx, high_idx = 0, H - 1
    elif left is not None and right is not None:
        axis = 'col'
        low_color, high_color = left, right
        low_idx, high_idx = 0, W - 1
    else:
        return {}

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != marker:
                continue
            pos = r if axis == 'row' else c
            if abs(pos - low_idx) <= abs(pos - high_idx):
                T[(r, c)] = low_color
            else:
                T[(r, c)] = high_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
