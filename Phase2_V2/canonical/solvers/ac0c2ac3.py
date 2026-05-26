from collections import Counter


def infer_T(input_grid):
    """Compute the latent transformation mask of concentric color rings.

    The grid is odd-sized and square-ish with a single background color and a
    set of scattered colored markers. Each marker sits at a unique Chebyshev
    distance from the grid center; that distance is the radius of the ring it
    must be painted at (distance 0 -> center pixel, 1 -> 3x3 ring, ...).
    """
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]
    cr, cc = (H - 1) / 2.0, (W - 1) / 2.0

    # Each colored marker defines the color for its ring (Chebyshev radius).
    ring_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            dist = int(max(abs(r - cr), abs(c - cc)))
            ring_color[dist] = v

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            dist = int(max(abs(r - cr), abs(c - cc)))
            if dist in ring_color:
                T[r][c] = ring_color[dist]
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
