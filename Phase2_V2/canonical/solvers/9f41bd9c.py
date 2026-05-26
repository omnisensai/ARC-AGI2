def infer_T(input_grid):
    """Infer the latent overwrite mask T (dict {(r,c): new_color}).

    Structure: a 5-coloured 'comet' = a solid head (2 full rows, width 5) plus
    teeth (alternating 5/1 columns) hanging below it, sitting against one
    vertical wall. A 6-region forms the floor below.

    Transformation: the comet launches horizontally to the OPPOSITE wall (head
    block re-anchored there, same rows). Its teeth trail back toward the origin
    wall, the tooth pattern shifting by one column per row of descent. The comet
    trail projects one extra row onto the 6 floor's top row, and from that
    projected tip a 9-line is drawn across the floor toward the origin wall.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    rows5 = [r for r in range(H) if any(input_grid[r][c] == 5 for c in range(W))]
    objcols = [c for c in range(W) if any(input_grid[r][c] == 5 for r in range(H))]

    # head rows = rows where every object column is a 5 (the solid block)
    head_rows = [r for r in rows5 if all(input_grid[r][c] == 5 for c in objcols)]
    tooth_rows = sorted(r for r in rows5 if r not in head_rows)

    # tooth column offsets relative to the head's left edge
    tcols = [c for c in objcols if any(input_grid[r][c] == 5 for r in tooth_rows)]
    base = min(objcols)
    tooth_offsets = sorted(c - base for c in tcols)
    width = len(objcols)

    # which wall is the head against, and where the 6 floor starts
    head_left = (min(objcols) == 0)
    sixtop = None
    for r in range(H):
        if all(input_grid[r][c] == 6 for c in range(W)):
            sixtop = r
            break

    T = {}

    # erase the original comet
    for r in rows5:
        for c in objcols:
            if input_grid[r][c] == 5:
                T[(r, c)] = 1

    # head launches to opposite wall; teeth trail toward origin wall
    if head_left:
        new_head_left = W - width
        direction = -1          # trail left, origin wall = left
    else:
        new_head_left = 0
        direction = +1          # trail right, origin wall = right

    # solid head block at new wall
    for r in head_rows:
        for c in range(new_head_left, new_head_left + width):
            T[(r, c)] = 5

    # sheared teeth: row k below head shifts k columns in the trailing direction
    for k, r in enumerate(tooth_rows):
        for off in tooth_offsets:
            c = new_head_left + off + k * direction
            if 0 <= c < W:
                T[(r, c)] = 5

    # 9-line on the floor: project teeth one more row, fill to the origin wall
    if sixtop is not None and tooth_rows:
        ntooth = len(tooth_rows)
        proj = [new_head_left + off + ntooth * direction for off in tooth_offsets]
        if direction > 0:
            inner = min(proj)
            for c in range(inner, W):
                T[(sixtop, c)] = 9
        else:
            inner = max(proj)
            for c in range(0, inner + 1):
                T[(sixtop, c)] = 9

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
