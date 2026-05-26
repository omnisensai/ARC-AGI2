def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The cross line color: a color that forms a full horizontal row AND a full
    # vertical column. Find the horizontal arm (full row of one non-bg color).
    line_color = None
    h_row = None
    for r in range(H):
        nonbg = set(input_grid[r]) - {bg}
        if len(nonbg) == 1:
            cand = next(iter(nonbg))
            if all(input_grid[r][c] == cand for c in range(W)):
                line_color = cand
                h_row = r
                break

    # Find the vertical arm (full column of the same line color).
    v_col = None
    if line_color is not None:
        for c in range(W):
            if all(input_grid[r][c] == line_color for r in range(H)):
                v_col = c
                break

    # Markers: any cell that is neither bg nor line color. Their count is the
    # shift magnitude (vertical arm moves left, horizontal arm moves down).
    marker_cells = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != line_color:
                marker_cells.append((r, c))
    shift = len(marker_cells)

    T = {}
    if line_color is None or v_col is None:
        return T

    new_col = v_col - shift
    new_row = h_row + shift

    # Erase old cross arms and markers.
    for r in range(H):
        T[(r, v_col)] = bg
    for c in range(W):
        T[(h_row, c)] = bg
    for (r, c) in marker_cells:
        T[(r, c)] = bg

    # Draw the shifted cross.
    if 0 <= new_col < W:
        for r in range(H):
            T[(r, new_col)] = line_color
    if 0 <= new_row < H:
        for c in range(W):
            T[(new_row, c)] = line_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
