def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid
    # Locate the diamond of 2s -> center, radius (Manhattan).
    twos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 2]
    rs = [r for r, c in twos]
    cs = [c for r, c in twos]
    cr = (min(rs) + max(rs)) / 2.0
    cc = (min(cs) + max(cs)) / 2.0
    R = max(abs(r - cr) + abs(c - cc) for r, c in twos)

    def interior(r, c):
        return abs(r - cr) + abs(c - cc) < R

    T = {}  # latent mask: (r, c) -> new color

    def shoot(sr, sc, dr, dc, color):
        # Travel inward from the border. Fill interior 0-cells with color,
        # pass through the diamond edge (2s), and stop at any interior obstacle.
        r, c = sr + dr, sc + dc
        while 0 <= r < H and 0 <= c < W:
            v = g[r][c]
            if interior(r, c):
                if v == 0:
                    T[(r, c)] = color
                elif v == 2:
                    pass  # crossing the diamond edge inward
                else:
                    break  # obstacle stops the ray
            r += dr
            c += dc

    # Border ray sources (non-zero, non-2) emit a ray perpendicular to their
    # border, traveling inward across the diamond.
    for c in range(W):
        if g[0][c] not in (0, 2):
            shoot(0, c, 1, 0, g[0][c])
        if g[H - 1][c] not in (0, 2):
            shoot(H - 1, c, -1, 0, g[H - 1][c])
    for r in range(H):
        if g[r][0] not in (0, 2):
            shoot(r, 0, 0, 1, g[r][0])
        if g[r][W - 1] not in (0, 2):
            shoot(r, W - 1, 0, -1, g[r][W - 1])
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
