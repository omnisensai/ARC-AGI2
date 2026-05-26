def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # collect non-background points by color
    pts = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                pts.setdefault(v, []).append((r, c))

    # build segments: each color = a pair of dots sharing a row or column
    h_segs = []  # horizontal: (row, c0, c1, color)
    v_segs = []  # vertical: (col, r0, r1, color)
    for color, cells in pts.items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        if r0 == r1:
            h_segs.append((r0, min(c0, c1), max(c0, c1), color))
        elif c0 == c1:
            v_segs.append((c0, min(r0, r1), max(r0, r1), color))

    # latent mask; verticals drawn first, horizontals do not overwrite verticals
    T = [[None] * W for _ in range(H)]
    for col, r0, r1, color in v_segs:
        for r in range(r0, r1 + 1):
            T[r][col] = color
    for row, c0, c1, color in h_segs:
        for c in range(c0, c1 + 1):
            if T[row][c] is None:
                T[row][c] = color
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
