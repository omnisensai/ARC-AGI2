def infer_T(input_grid):
    """Two perpendicular colored bands cross. One band ('line') spans the entire
    grid in one direction (a set of full rows OR full columns of a single color).
    The other band ('stripe') is perpendicular and is interrupted where the line
    crosses it. The transformation lets the stripe pass through: every cell that
    belongs to the line band AND lies in a stripe column/row is overwritten with
    the stripe color. T maps those intersection cells -> stripe color.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    cnt = {}
    for row in input_grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    bg = max(cnt, key=cnt.get)

    # full rows / full columns (each entirely a single color)
    full_rows = [r for r in range(H) if len(set(input_grid[r])) == 1]
    full_cols = [c for c in range(W)
                 if len(set(input_grid[r][c] for r in range(H))) == 1]

    if full_rows:
        line_dir = 'row'
        line_idx = full_rows
        line_color = input_grid[full_rows[0]][0]
    elif full_cols:
        line_dir = 'col'
        line_idx = full_cols
        line_color = input_grid[0][full_cols[0]]
    else:
        return {}

    # stripe color: the non-background, non-line color present in the grid
    stripe_color = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != line_color:
                stripe_color = v
                break
        if stripe_color is not None:
            break
    if stripe_color is None:
        return {}

    T = {}
    if line_dir == 'row':
        # stripe occupies whole columns where stripe_color appears
        stripe_cols = [c for c in range(W)
                       if any(input_grid[r][c] == stripe_color for r in range(H))]
        for r in line_idx:
            for c in stripe_cols:
                T[(r, c)] = stripe_color
    else:
        # stripe occupies whole rows where stripe_color appears
        stripe_rows = [r for r in range(H)
                       if any(input_grid[r][c] == stripe_color for c in range(W))]
        for c in line_idx:
            for r in stripe_rows:
                T[(r, c)] = stripe_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
