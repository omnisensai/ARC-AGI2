def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Find the two markers (non-zero cells on a 0 background).
    markers = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W)
               if input_grid[r][c] != 0]
    T = [[None] * W for _ in range(H)]
    if len(markers) != 2:
        return T
    (r1, c1, v1), (r2, c2, v2) = markers
    dr = abs(r1 - r2)
    dc = abs(c1 - c2)
    # The smaller POSITIVE gap defines the tiling axis. A zero gap means the two
    # markers share that coordinate, so it cannot be the tiling axis.
    use_rows = (dr > 0) and (dc == 0 or dr <= dc)
    if use_rows:
        # Vertical separation -> full-row (horizontal) lines, tiled downward
        # with period 2*gap, alternating the two marker colors.
        if r1 <= r2:
            start, gap, va, vb = r1, dr, v1, v2
        else:
            start, gap, va, vb = r2, dr, v2, v1
        k = 0
        r = start
        while r < H:
            color = va if k % 2 == 0 else vb
            for c in range(W):
                T[r][c] = color
            k += 1
            r = start + k * gap
    else:
        # Horizontal separation -> full-column (vertical) lines, tiled rightward
        # with period 2*gap, alternating the two marker colors.
        gap = dc
        if gap == 0:
            return T
        if c1 <= c2:
            start, va, vb = c1, v1, v2
        else:
            start, va, vb = c2, v2, v1
        k = 0
        c = start
        while c < W:
            color = va if k % 2 == 0 else vb
            for r in range(H):
                T[r][c] = color
            k += 1
            c = start + k * gap
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
