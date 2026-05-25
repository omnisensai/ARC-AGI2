def infer_T(input_grid):
    """Locate the 3x3 colored block; from its center, each of the 8
    surrounding cells emits a ray in its (dr,dc) direction to the grid
    edge, painted with that neighbor's color. Returns a latent mask
    {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    cr = (r0 + r1) // 2  # center row of the block
    cc = (c0 + c1) // 2  # center col of the block
    T = {}
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue  # center cell is preserved
            sr, sc = cr + dr, cc + dc
            if not (0 <= sr < H and 0 <= sc < W):
                continue
            color = input_grid[sr][sc]
            if color == 0:
                continue
            r, c = sr, sc
            while 0 <= r < H and 0 <= c < W:
                T[(r, c)] = color
                r += dr
                c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
