def infer_T(input_grid):
    """Infer the latent transformation mask.

    Inside the 7-canvas there is an arrow: a shaft of 6s leading to a single
    2-head. The arrow points in the direction from the shaft toward the head.
    A ray is fired from the head in that direction; the first cell outside the
    7-canvas (the first non-7 cell the ray reaches) is recolored to 7.
    """
    H, W = len(input_grid), len(input_grid[0])

    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    twos = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]

    T = {}
    if not twos or not sixes:
        return T

    head = twos[0]
    # nearest shaft cell to the head defines the pointing direction
    near = min(sixes, key=lambda s: (s[0] - head[0]) ** 2 + (s[1] - head[1]) ** 2)
    sign = lambda x: (x > 0) - (x < 0)
    dr = sign(head[0] - near[0])
    dc = sign(head[1] - near[1])
    if dr == 0 and dc == 0:
        return T

    r, c = head
    while True:
        r += dr
        c += dc
        if not (0 <= r < H and 0 <= c < W):
            break
        if input_grid[r][c] != 7:
            T[(r, c)] = 7
            break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
