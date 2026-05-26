def infer_T(input_grid):
    """Compute the latent transformation mask.

    Background is the most common color (0). Every other color appears at
    exactly two cells which lie on a perfect diagonal. The transformation
    draws the full diagonal segment connecting each such pair, in that
    color. The mask T is a dict {(r,c): new_color}.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    endpoints = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                endpoints.setdefault(v, []).append((r, c))

    T = {}
    for color, pts in endpoints.items():
        if len(pts) != 2:
            continue
        (r1, c1), (r2, c2) = pts
        if abs(r1 - r2) != abs(c1 - c2):
            continue  # not a clean diagonal; skip
        n = abs(r1 - r2)
        dr = (r2 > r1) - (r2 < r1)
        dc = (c2 > c1) - (c2 < c1)
        for i in range(n + 1):
            T[(r1 + i * dr, c1 + i * dc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
