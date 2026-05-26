def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cells = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg]

    # Triangle is the dominant non-bg color; the marker is the singleton color
    # embedded in it (at the center of the triangle's flat base).
    ccount = {}
    for r, c, v in cells:
        ccount[v] = ccount.get(v, 0) + 1
    tri_color = max(ccount, key=ccount.get)
    marker_color = min(ccount, key=ccount.get)
    marker = next((r, c) for r, c, v in cells if v == marker_color)
    mr, mc = marker

    tri = [(r, c) for r, c, v in cells if v == tri_color]
    rs = [r for r, c in tri]
    cs = [c for r, c in tri]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)

    # The triangle points away from its base. The marker lies on the base edge;
    # the ray shoots in the pointing direction (toward apex and out to the edge).
    if mr == rmax and rmax != rmin:      # base at bottom -> points up
        dr, dc = -1, 0
    elif mr == rmin and rmax != rmin:    # base at top -> points down
        dr, dc = 1, 0
    elif mc == cmax and cmax != cmin:    # base at right -> points left
        dr, dc = 0, -1
    elif mc == cmin and cmax != cmin:    # base at left -> points right
        dr, dc = 0, 1
    else:
        dr, dc = 0, 0

    # Paint the marker-colored ray over background cells from the marker,
    # in the pointing direction, until the grid edge.
    T = {}
    r, c = mr + dr, mc + dc
    while 0 <= r < H and 0 <= c < W:
        if input_grid[r][c] == bg:
            T[(r, c)] = marker_color
        r += dr
        c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
