def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    def row_bg(r):
        return set(v for v in input_grid[r] if v != 0)

    def col_bg(c):
        return set(input_grid[r][c] for r in range(H) if input_grid[r][c] != 0)

    horizontal_ok = all(len(row_bg(r)) <= 1 for r in range(H))
    vertical_ok = all(len(col_bg(c)) <= 1 for c in range(W))

    T = {}
    if horizontal_ok and not vertical_ok:
        # Grid is split into horizontal bands (contiguous rows of one bg color).
        # Each 0 marker extends vertically across its whole band.
        bands = []
        r = 0
        while r < H:
            color = next((v for v in input_grid[r] if v != 0), None)
            r0 = r
            while r < H and next((v for v in input_grid[r] if v != 0), color) == color:
                r += 1
            bands.append((r0, r - 1))
        for (r0, r1) in bands:
            cols = set()
            for rr in range(r0, r1 + 1):
                for c in range(W):
                    if input_grid[rr][c] == 0:
                        cols.add(c)
            for c in cols:
                for rr in range(r0, r1 + 1):
                    T[(rr, c)] = 0
    elif vertical_ok:
        # Grid is split into vertical bands (contiguous cols of one bg color).
        # Each 0 marker extends horizontally across its whole band.
        bands = []
        c = 0
        while c < W:
            color = next((input_grid[r][c] for r in range(H) if input_grid[r][c] != 0), None)
            c0 = c
            while c < W:
                cc_color = next((input_grid[r][c] for r in range(H) if input_grid[r][c] != 0), color)
                if cc_color != color:
                    break
                c += 1
            bands.append((c0, c - 1))
        for (c0, c1) in bands:
            rows = set()
            for cc in range(c0, c1 + 1):
                for r in range(H):
                    if input_grid[r][cc] == 0:
                        rows.add(r)
            for r in rows:
                for cc in range(c0, c1 + 1):
                    T[(r, cc)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
