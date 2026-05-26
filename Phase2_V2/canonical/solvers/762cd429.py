def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    pos = None
    for r in range(H - 1):
        for c in range(W - 1):
            if (input_grid[r][c] != 0 and input_grid[r][c + 1] != 0
                    and input_grid[r + 1][c] != 0 and input_grid[r + 1][c + 1] != 0):
                pos = (r, c)
                break
        if pos is not None:
            break
    T = {}
    if pos is None:
        return T
    r0, c0 = pos
    TL = input_grid[r0][c0]
    TR = input_grid[r0][c0 + 1]
    BL = input_grid[r0 + 1][c0]
    BR = input_grid[r0 + 1][c0 + 1]
    yc = r0 + 1
    left = c0
    k = 0
    while True:
        sz = 2 ** (k + 1)
        half = sz // 2
        top = yc - half
        right = left + sz - 1
        if top < 0 or top + sz - 1 >= H or right >= W:
            break
        for dr in range(sz):
            rr = top + dr
            for dc in range(sz):
                cc = left + dc
                if dr < half:
                    color = TL if dc < half else TR
                else:
                    color = BL if dc < half else BR
                T[(rr, cc)] = color
        left = right + 1
        k += 1
    return T

def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out

def solve(input_grid):
    return apply_T(input_grid, infer_T(input_grid))
