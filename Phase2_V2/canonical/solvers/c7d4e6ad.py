def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Identify the "shape" color: a single non-bg color that forms the figure
    # to be recolored. It's the color whose cells are NOT the per-row markers.
    # Markers live in a single column (typically leftmost non-bg column);
    # the shape color is recolored per-row using the marker color of that row.

    # Find candidate marker color: appears in many rows within one column.
    # Find the shape color as the most common non-bg color that is uniform.
    color_cols = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            color_cols.setdefault(v, set()).add(c)

    # Shape color: the color occupying the widest spread of columns (the figure).
    shape_color = max(color_cols, key=lambda v: len(color_cols[v]))

    # Per-row marker color: the leftmost non-bg, non-shape cell in each row.
    row_marker = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != shape_color:
                row_marker[r] = v
                break

    # Build mask: every shape cell recolored to its row's marker color.
    T = {}
    for r in range(H):
        if r not in row_marker:
            continue
        mc = row_marker[r]
        for c in range(W):
            if input_grid[r][c] == shape_color:
                T[(r, c)] = mc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
