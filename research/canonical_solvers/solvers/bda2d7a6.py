"""Canonical solver for ARC puzzle bda2d7a6.

The grid is a set of concentric square rings, each a single color.
The transformation reverses the order of the ring colors: a cell whose
ring index is i (0 = outermost) gets the color of ring n-1-i.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Ring index of a cell = its Chebyshev distance from the nearest border.
    def ring_of(r, c):
        return min(r, c, H - 1 - r, W - 1 - c)

    max_ring = min((H - 1) // 2, (W - 1) // 2)

    # Determine the color of each ring (sampling a representative cell).
    ring_color = {}
    for r in range(H):
        for c in range(W):
            k = ring_of(r, c)
            ring_color.setdefault(k, input_grid[r][c])

    n = max_ring + 1
    # Reversed mapping: ring k takes the color of ring (n-1-k).
    color_map = {k: ring_color[n - 1 - k] for k in range(n)}

    # Build latent mask: every cell gets its reversed ring color.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            T[r][c] = color_map[ring_of(r, c)]
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
