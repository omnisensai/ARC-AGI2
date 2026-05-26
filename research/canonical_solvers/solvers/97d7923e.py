from collections import defaultdict


def infer_T(input_grid):
    H = len(input_grid); W = len(input_grid[0])

    def col_bars(c):
        col = [input_grid[r][c] for r in range(H)]
        out = []; r = 0
        while r < H:
            if col[r] != 0:
                s = r
                while r < H and col[r] != 0:
                    r += 1
                out.append((s, r - 1, col[s:r]))
            else:
                r += 1
        return out

    legends = {}   # cap color -> max length of a monochrome (legend) bar
    therms = []    # (col, s, e, cap)
    for c in range(W):
        for s, e, seg in col_bars(c):
            cap = seg[0]
            interior = set(seg[1:-1])
            is_therm = (len(seg) >= 3 and seg[0] == seg[-1] and
                        interior and interior != {cap})
            if is_therm:
                therms.append((c, s, e, cap))
            elif len(set(seg)) == 1:
                legends[cap] = max(legends.get(cap, 0), len(seg))

    grp = defaultdict(list)
    for c, s, e, cap in therms:
        grp[cap].append((c, s, e))

    T = {}
    for cap, lst in grp.items():
        if cap not in legends:
            continue
        L = legends[cap]
        lst.sort(key=lambda b: -(b[2] - b[1] + 1))  # descending length
        if 1 <= L <= len(lst):
            c, s, e = lst[L - 1]
            for r in range(s, e + 1):
                T[(r, c)] = cap
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
