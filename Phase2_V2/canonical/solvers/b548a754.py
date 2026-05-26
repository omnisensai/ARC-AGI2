def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # find the 8 marker
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 8:
                marker = (r, c)

    # bounding box of the rectangle object (non-bg, non-8 cells)
    cells = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg and input_grid[r][c] != 8]
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)

    # border color = outer ring color; inner color = interior fill
    border = input_grid[r0][c0]
    inner = None
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            inner = input_grid[r][c]
    if inner is None:
        inner = border

    # extend the box edge toward the marker so it lands on the marker's row/col
    nr0, nr1, nc0, nc1 = r0, r1, c0, c1
    if marker is not None:
        mr, mc = marker
        if mc > c1:        # marker to the right
            nc1 = mc
        elif mc < c0:      # marker to the left
            nc0 = mc
        elif mr > r1:      # marker below
            nr1 = mr
        elif mr < r0:      # marker above
            nr0 = mr

    # latent mask: draw new rectangle (border ring + inner fill), erase marker
    T = {}
    for r in range(nr0, nr1 + 1):
        for c in range(nc0, nc1 + 1):
            if r in (nr0, nr1) or c in (nc0, nc1):
                T[(r, c)] = border
            else:
                T[(r, c)] = inner
    if marker is not None and marker not in T:
        T[marker] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
