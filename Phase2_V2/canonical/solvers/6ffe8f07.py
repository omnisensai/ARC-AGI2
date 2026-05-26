def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): color}.

    Rule: a single rectangular block of color 8 acts as an emitter. From every
    column of the block a ray of color 4 is shot straight up and down; from every
    row a ray is shot left and right. Each ray fills cells with 4, passing
    through background (0) and color-2 shapes (overwriting them), but is blocked
    by color-1 shapes: it stops just before the first 1 it encounters, and the 1
    (and everything beyond it along that ray) is preserved.
    """
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    T = {}
    if not cells:
        return T
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    RAY, BLOCKER = 4, 1

    def shoot(r, c, dr, dc):
        r += dr
        c += dc
        while 0 <= r < H and 0 <= c < W:
            if input_grid[r][c] == BLOCKER:
                break
            T[(r, c)] = RAY
            r += dr
            c += dc

    for c in range(c0, c1 + 1):
        shoot(r0, c, -1, 0)
        shoot(r1, c, 1, 0)
    for r in range(r0, r1 + 1):
        shoot(r, c0, 0, -1)
        shoot(r, c1, 0, 1)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
