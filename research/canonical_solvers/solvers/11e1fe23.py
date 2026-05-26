def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    pts = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W)
           if input_grid[r][c] != bg]
    T = {}
    if len(pts) != 3:
        return T
    # Identify the corner: the point that shares its row with one other point
    # and its column with another (the three points form an L / right angle).
    corner = armR = armC = None
    for p in pts:
        r, c, v = p
        sr = [q for q in pts if q[0] == r and q != p]   # same row neighbour
        sc = [q for q in pts if q[1] == c and q != p]   # same column neighbour
        if sr and sc:
            corner, armR, armC = p, sr[0], sc[0]
    if corner is None:
        return T
    cr, cc, cv = corner
    # Diagonal direction the corner opens toward (toward the two arm endpoints).
    dr = 1 if armC[0] > cr else -1
    dc = 1 if armR[1] > cc else -1
    # New (small) corner placed at the centroid of the three points (rounded).
    ncr = round((pts[0][0] + pts[1][0] + pts[2][0]) / 3)
    ncc = round((pts[0][1] + pts[1][1] + pts[2][1]) / 3)
    # A half-scale L replica around the new corner: corner colour at the new
    # corner, each arm colour two steps along its axis, and a 5 at the
    # diagonal centre (one step inward).
    placements = [
        (ncr, ncc, cv),                  # corner colour at new corner
        (ncr, ncc + 2 * dc, armR[2]),    # row-arm colour, two along the row dir
        (ncr + 2 * dr, ncc, armC[2]),    # col-arm colour, two along the col dir
        (ncr + dr, ncc + dc, 5),         # 5 at the diagonal centre
    ]
    for r, c, v in placements:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
