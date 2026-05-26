def infer_T(input_grid):
    """Concentric square rings: build a mask that recolors each ring with the
    color from the ring at the mirrored depth (outermost <-> innermost)."""
    H, W = len(input_grid), len(input_grid[0])
    # depth of a cell = Chebyshev distance to the nearest border edge.
    depth_color = {}
    for r in range(H):
        for c in range(W):
            d = min(r, c, H - 1 - r, W - 1 - c)
            depth_color.setdefault(d, input_grid[r][c])
    D = max(depth_color)
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            d = min(r, c, H - 1 - r, W - 1 - c)
            T[r][c] = depth_color[D - d]
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
