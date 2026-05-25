def infer_T(input_grid):
    """Place a border-colored marker one step from each '1' toward the nearer
    of the two parallel border lines."""
    g = input_grid
    H, W = len(g), len(g[0])

    # Detect uniform full-line borders (single nonzero color).
    top = bot = left = right = None
    top_c = bot_c = left_c = right_c = None
    if g[0][0] != 0 and all(g[0][c] == g[0][0] for c in range(W)):
        top, top_c = 0, g[0][0]
    if g[H-1][0] != 0 and all(g[H-1][c] == g[H-1][0] for c in range(W)):
        bot, bot_c = H-1, g[H-1][0]
    if g[0][0] != 0 and all(g[r][0] == g[0][0] for r in range(H)):
        left, left_c = 0, g[0][0]
    if g[0][W-1] != 0 and all(g[r][W-1] == g[0][W-1] for r in range(H)):
        right, right_c = W-1, g[0][W-1]

    horizontal = top is not None and bot is not None
    vertical = left is not None and right is not None

    T = {}  # latent mask: {(r,c): new_color}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 1:
                continue
            if horizontal:
                if (r - top) <= (bot - r):
                    T[(r - 1, c)] = top_c
                else:
                    T[(r + 1, c)] = bot_c
            elif vertical:
                if (c - left) <= (right - c):
                    T[(r, c - 1)] = left_c
                else:
                    T[(r, c + 1)] = right_c
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
