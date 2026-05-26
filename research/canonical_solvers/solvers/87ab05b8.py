def infer_T(input_grid):
    """Latent mask: the whole grid becomes background except the quadrant that
    contains the marker color 2, which is filled solid with 2."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # locate the single marker cell of color 2
    pos = next(((r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] == 2), None)
    T = [[bg] * W for _ in range(H)]
    if pos is None:
        return T
    mr, mc = pos
    midH, midW = H // 2, W // 2
    r0, r1 = (0, midH) if mr < midH else (midH, H)
    c0, c1 = (0, midW) if mc < midW else (midW, W)
    for r in range(r0, r1):
        for c in range(c0, c1):
            T[r][c] = 2
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
