def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure of every pair: four L-shaped corner markers define one rectangle.
    Three corners are made of color 8; the fourth is an L of some other color X.
    The output draws the full rectangle frame in 8, fills its interior with X, and
    extends X-colored strips outward from each side of the box to the grid edges.
    Any scattered single cell sitting inside one of those strip bands projects its
    own color from itself outward to the far grid edge (overwriting the X strip).
    """
    H = len(input_grid); W = len(input_grid[0])

    def comps(color):
        seen = set(); res = []
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] == color and (r, c) not in seen:
                    stack = [(r, c)]; comp = []
                    while stack:
                        y, x = stack.pop()
                        if (y, x) in seen or not (0 <= y < H and 0 <= x < W) or input_grid[y][x] != color:
                            continue
                        seen.add((y, x)); comp.append((y, x))
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                if dy or dx:
                                    stack.append((y + dy, x + dx))
                    res.append(comp)
        return res

    eights = comps(8)
    allcells = [cell for comp in eights for cell in comp]
    rs = [r for r, c in allcells]; cs = [c for r, c in allcells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    # The corner of the bounding box that is NOT occupied by an 8 holds the
    # differently-colored L marker; its color is the box fill color.
    corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
    missing = [(cr, cc) for (cr, cc) in corners if input_grid[cr][cc] != 8]
    mr, mc = missing[0]
    fill = input_grid[mr][mc]

    T = {}
    # interior fill
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            T[(r, c)] = fill
    # rectangle frame
    for c in range(c0, c1 + 1):
        T[(r0, c)] = 8; T[(r1, c)] = 8
    for r in range(r0, r1 + 1):
        T[(r, c0)] = 8; T[(r, c1)] = 8
    # strips out to the grid edges, fill color
    for r in range(r0, r1 + 1):
        for c in range(0, c0):
            T[(r, c)] = fill
        for c in range(c1 + 1, W):
            T[(r, c)] = fill
    for c in range(c0, c1 + 1):
        for r in range(0, r0):
            T[(r, c)] = fill
        for r in range(r1 + 1, H):
            T[(r, c)] = fill

    # projections of scattered cells within the strip bands toward the far edge
    proj = []
    for r in range(r0, r1 + 1):
        for c in range(0, c0):
            if input_grid[r][c] != 0:
                proj.append(('L', r, c, input_grid[r][c]))
        for c in range(c1 + 1, W):
            if input_grid[r][c] != 0:
                proj.append(('R', r, c, input_grid[r][c]))
    for c in range(c0, c1 + 1):
        for r in range(0, r0):
            if input_grid[r][c] != 0:
                proj.append(('T', r, c, input_grid[r][c]))
        for r in range(r1 + 1, H):
            if input_grid[r][c] != 0:
                proj.append(('B', r, c, input_grid[r][c]))

    def dist_to_box(item):
        d, r, c, v = item
        if d == 'L': return c0 - c
        if d == 'R': return c - c1
        if d == 'T': return r0 - r
        return r - r1

    # paint nearest-box first so cells nearer the far edge win any overlap
    proj.sort(key=dist_to_box)
    for d, r, c, v in proj:
        if d == 'L':
            for cc in range(0, c + 1): T[(r, cc)] = v
        elif d == 'R':
            for cc in range(c, W): T[(r, cc)] = v
        elif d == 'T':
            for rr in range(0, r + 1): T[(rr, c)] = v
        else:
            for rr in range(r, H): T[(rr, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
