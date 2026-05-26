def infer_T(input_grid):
    """Find each rectangle of 8s and compute a recolor mask:
    quadrant colors (TL=6, TR=1, BL=2, BR=3) with an inner inset-2
    region overwritten to 4."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 8 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] \
                                and input_grid[nr][nc] == 8:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    T = {}
    for cells in comps:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        nrows = r1 - r0 + 1
        ncols = c1 - c0 + 1
        midr = r0 + nrows // 2   # first row of bottom half
        midc = c0 + ncols // 2   # first col of right half
        inset = 2
        ir0, ir1 = r0 + inset, r1 - inset
        ic0, ic1 = c0 + inset, c1 - inset
        for (rr, cc) in cells:
            top = rr < midr
            left = cc < midc
            if top and left:
                col = 6
            elif top and not left:
                col = 1
            elif (not top) and left:
                col = 2
            else:
                col = 3
            if ir0 <= rr <= ir1 and ic0 <= cc <= ic1:
                col = 4
            T[(rr, cc)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
