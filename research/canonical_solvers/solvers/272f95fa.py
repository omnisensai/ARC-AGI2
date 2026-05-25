def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # full rows/cols of 8 act as separator lines dividing the grid into bands
    sep_rows = [r for r in range(H) if all(input_grid[r][c] == 8 for c in range(W))]
    sep_cols = [c for c in range(W) if all(input_grid[r][c] == 8 for r in range(H))]

    def bands(n, seps):
        bs = []
        start = 0
        for s in seps:
            if s > start:
                bs.append((start, s - 1))
            start = s + 1
        if start <= n - 1:
            bs.append((start, n - 1))
        return bs

    rbands = bands(H, sep_rows)
    cbands = bands(W, sep_cols)

    # center band is the middle one along each axis
    ri = len(rbands) // 2
    ci = len(cbands) // 2

    T = {}
    for bi, (r0, r1) in enumerate(rbands):
        for bj, (c0, c1) in enumerate(cbands):
            dr = bi - ri  # <0 above center, 0 center row, >0 below
            dc = bj - ci  # <0 left of center, 0 center col, >0 right
            if dr == 0 and dc == 0:
                color = 6
            elif dr == 0 and dc < 0:
                color = 4
            elif dr == 0 and dc > 0:
                color = 3
            elif dr < 0 and dc == 0:
                color = 2
            elif dr > 0 and dc == 0:
                color = 1
            else:
                color = None  # corner regions unchanged
            if color is not None:
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
