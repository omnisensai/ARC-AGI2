def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    # marker = the non-background, non-5 color forming the diagonal
    marker = None
    for v in counts:
        if v not in (0, 5):
            marker = v
            break
    T = {}
    if marker is None:
        return T
    # erase all the 5 "thickness" cells
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 5:
                T[(r, c)] = 0
    # the marker lies on a single down-right diagonal (constant c - r)
    mdiags = sorted(set(c - r for r in range(H) for c in range(W)
                        if input_grid[r][c] == marker))
    base = mdiags[0]
    out_diags = set(mdiags)  # the original marker diagonal is kept
    # 5s form triangular wedges on one or both sides of the marker diagonal.
    # each wedge of T(n)=n(n+1)/2 cells spawns one parallel diagonal offset
    # by (n + 2) toward that side.
    left = [(r, c) for r in range(H) for c in range(W)
            if input_grid[r][c] == 5 and (c - r) < base]
    right = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] == 5 and (c - r) > base]

    def tri_n(cells):
        n = 0
        while n * (n + 1) // 2 < len(cells):
            n += 1
        return n

    if left:
        out_diags.add(base - (tri_n(left) + 2))
    if right:
        out_diags.add(base + (tri_n(right) + 2))
    # paint every full down-right diagonal (c - r = dval) in the marker color
    for dval in out_diags:
        for r in range(H):
            c = r + dval
            if 0 <= c < W:
                T[(r, c)] = marker
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
