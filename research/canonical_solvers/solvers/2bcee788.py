def infer_T(input_grid):
    """Infer the latent transformation mask.

    Structure: a coloured shape (one non-zero colour != 2) plus a straight line
    of marker cells coloured 2 sitting on one side of the shape.  The marker
    line is a mirror axis: the shape is reflected across the line that lies
    halfway between the marker line and the adjacent shape cells, and the union
    of the shape with its reflection is drawn.  The whole background (0) becomes
    3.  Returns a dict {(r,c): colour}.
    """
    H, W = len(input_grid), len(input_grid[0])

    cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                cells.setdefault(v, []).append((r, c))

    twos = cells.get(2, [])
    shape_colors = [k for k in cells if k != 2]

    T = {}
    # repaint entire background to 3
    for r in range(H):
        for c in range(W):
            T[(r, c)] = 3

    if not shape_colors or not twos:
        return T

    color = shape_colors[0]
    shape = cells[color]

    rows2 = {r for r, c in twos}
    cols2 = {c for r, c in twos}

    drawn = set(shape)

    if len(rows2) == 1:
        # horizontal marker line -> reflect vertically across a row axis
        rline = next(iter(rows2))
        shape_rows = [r for r, c in shape]
        if shape_rows:
            # shape sits on one side of the marker row; axis = halfway between
            if min(shape_rows) >= rline:
                axis2 = (rline + min(shape_rows))      # 2*axis
            else:
                axis2 = (rline + max(shape_rows))
            for (r, c) in shape:
                drawn.add((axis2 - r, c))
    elif len(cols2) == 1:
        # vertical marker line -> reflect horizontally across a column axis
        cline = next(iter(cols2))
        shape_cols = [c for r, c in shape]
        if shape_cols:
            if min(shape_cols) >= cline:
                axis2 = (cline + min(shape_cols))
            else:
                axis2 = (cline + max(shape_cols))
            for (r, c) in shape:
                drawn.add((r, axis2 - c))

    for (r, c) in drawn:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
