def _find_objects(g):
    """Connected same-color (non-background) rectangles -> list of (color, minr, maxr, minc, maxc)."""
    H, W = len(g), len(g[0])
    bg = 7
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or g[rr][cc] != col:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                rs = [x[0] for x in cells]
                cs = [x[1] for x in cells]
                objs.append((col, min(rs), max(rs), min(cs), max(cs)))
    return objs


def infer_T(input_grid):
    """For each color (appearing as exactly two squares positioned along a diagonal),
    draw a diagonal line in the gap connecting the two facing corners. Returns a
    latent mask dict {(r,c): color}."""
    H, W = len(input_grid), len(input_grid[0])
    objs = _find_objects(input_grid)
    by_color = {}
    for o in objs:
        by_color.setdefault(o[0], []).append(o)

    T = {}
    for col, group in by_color.items():
        if len(group) != 2:
            continue
        group = sorted(group, key=lambda o: (o[1], o[3]))
        A, B = group
        ar = (A[1] + A[2]) / 2.0
        ac = (A[3] + A[4]) / 2.0
        br = (B[1] + B[2]) / 2.0
        bc = (B[3] + B[4]) / 2.0
        dr = 1 if br > ar else -1 if br < ar else 0
        dc = 1 if bc > ac else -1 if bc < ac else 0
        if dr == 0 or dc == 0:
            continue  # only diagonal pairs

        # facing corner of A (the corner pointing toward B)
        a_r = A[2] if dr > 0 else A[1]
        a_c = A[4] if dc > 0 else A[3]
        # facing corner of B (the corner pointing toward A)
        b_r = B[1] if dr > 0 else B[2]
        b_c = B[3] if dc > 0 else B[4]

        # step diagonally into the gap until just before B's facing corner row
        r, c = a_r + dr, a_c + dc
        while r != b_r:
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = col
            r += dr
            c += dc
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
