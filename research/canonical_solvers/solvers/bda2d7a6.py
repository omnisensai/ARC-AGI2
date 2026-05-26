"""Canonical solver for ARC puzzle bda2d7a6.

The grid is a set of concentric square rings, each a single color. The
distinct ring colors form a sequence from outer to inner. The transformation
cyclically shifts that color sequence inward: each distinct color is remapped
to the color of the ring just outside it, and the outermost color wraps to the
position of the innermost. Equivalently, ring colors rotate one step outward.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Ring index of a cell = its Chebyshev distance from the nearest border.
    def ring_of(r, c):
        return min(r, c, H - 1 - r, W - 1 - c)

    max_ring = min((H - 1) // 2, (W - 1) // 2)
    n = max_ring + 1

    # Color of each ring (outer -> inner), sampled from a representative cell.
    ring_color = {}
    for r in range(H):
        for c in range(W):
            k = ring_of(r, c)
            ring_color.setdefault(k, input_grid[r][c])
    seq = [ring_color[k] for k in range(n)]

    # Distinct colors in outer->inner order.
    distinct = []
    for col in seq:
        if col not in distinct:
            distinct.append(col)

    # Cyclic shift: each distinct color maps to the color one position earlier
    # (innermost distinct color wraps out to the front).
    m = len(distinct)
    color_map = {distinct[i]: distinct[(i - 1) % m] for i in range(m)}

    # Build latent mask by recoloring every cell via the color map.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            T[r][c] = color_map[input_grid[r][c]]
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
