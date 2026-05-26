def infer_T(input_grid):
    """Locate the single non-background marker and grow it into the filled
    rectangle that spans from the marker to its nearest grid corner."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    marker = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                marker = (r, c)
                break
        if marker:
            break
    T = [[None] * W for _ in range(H)]
    if marker is None:
        return T
    r, c = marker
    color = input_grid[r][c]
    # Nearest vertical edge and nearest horizontal edge define the target corner.
    r_edge = 0 if r <= (H - 1 - r) else H - 1
    c_edge = 0 if c <= (W - 1 - c) else W - 1
    r0, r1 = min(r, r_edge), max(r, r_edge)
    c0, c1 = min(c, c_edge), max(c, c_edge)
    for rr in range(r0, r1 + 1):
        for cc in range(c0, c1 + 1):
            T[rr][cc] = color
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
