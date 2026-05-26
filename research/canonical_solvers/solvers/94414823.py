def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # locate the rectangular box of 5s
    fives = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    r0 = min(r for r, c in fives); r1 = max(r for r, c in fives)
    c0 = min(c for r, c in fives); c1 = max(c for r, c in fives)
    # interior (inside the 5 border)
    ir0, ir1 = r0 + 1, r1 - 1
    ic0, ic1 = c0 + 1, c1 - 1
    # split interior into four quadrants
    rmid = (ir0 + ir1 + 1) // 2
    cmid = (ic0 + ic1 + 1) // 2
    corners = {'TL': (r0, c0), 'TR': (r0, c1), 'BL': (r1, c0), 'BR': (r1, c1)}
    # markers: nonzero, non-5 cells outside the box
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0 or v == 5:
                continue
            if r0 <= r <= r1 and c0 <= c <= c1:
                continue
            markers.append((r, c, v))
    # each marker colors its nearest quadrant; diagonal-opposite quadrant copies it
    quad_color = {}
    for (r, c, v) in markers:
        best = min(corners, key=lambda k: (r - corners[k][0]) ** 2 + (c - corners[k][1]) ** 2)
        quad_color[best] = v
    opp = {'TL': 'BR', 'BR': 'TL', 'TR': 'BL', 'BL': 'TR'}
    for k in list(quad_color):
        quad_color[opp[k]] = quad_color[k]
    # build latent mask
    T = [[None] * W for _ in range(H)]

    def cells(q):
        rr = range(ir0, rmid) if q[0] == 'T' else range(rmid, ir1 + 1)
        cc = range(ic0, cmid) if q[1] == 'L' else range(cmid, ic1 + 1)
        return [(r, c) for r in rr for c in cc]

    for q, col in quad_color.items():
        for (r, c) in cells(q):
            T[r][c] = col
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
