def infer_T(input_grid):
    """Latent mask: for every cell, the color its concentric ring should become.

    The grid is organized as concentric rectangular rings (ring index =
    distance to the nearest border). Each ring is repaired/cleaned to a single
    uniform color: the most frequent non-background (non-0) color appearing in
    that ring of the input. Rings that contain only background stay background.
    """
    H, W = len(input_grid), len(input_grid[0])

    def ring_index(r, c):
        return min(r, c, H - 1 - r, W - 1 - c)

    max_ring = min(H, W) // 2 + 1

    # Determine the consensus color for each ring from the input cells.
    ring_color = {}
    for k in range(max_ring):
        counts = {}
        for r in range(H):
            for c in range(W):
                if ring_index(r, c) == k:
                    v = input_grid[r][c]
                    if v != 0:
                        counts[v] = counts.get(v, 0) + 1
        ring_color[k] = max(counts, key=counts.get) if counts else 0

    # Build the explicit transformation mask.
    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            T[r][c] = ring_color[ring_index(r, c)]
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
