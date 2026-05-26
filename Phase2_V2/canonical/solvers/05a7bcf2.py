def _find_full_lines(g):
    H, W = len(g), len(g[0])
    rows = {}
    for r in range(H):
        s = set(g[r])
        if len(s) == 1 and g[r][0] != 0:
            rows[r] = g[r][0]
    cols = {}
    for c in range(W):
        col = [g[r][c] for r in range(H)]
        s = set(col)
        if len(s) == 1 and col[0] != 0:
            cols[c] = col[0]
    return rows, cols


def _profile_run(positions, line):
    sset = set(positions)
    if line not in sset:
        return 1
    n = 1
    i = line - 1
    while i in sset:
        n += 1
        i -= 1
    i = line + 1
    while i in sset:
        n += 1
        i += 1
    return n


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    rows, cols = _find_full_lines(g)
    T = {}

    def put(r, c, v):
        T[(r, c)] = v

    if 8 in cols.values() and 2 in cols.values():
        line8 = [c for c, v in cols.items() if v == 8][0]
        line2 = [c for c, v in cols.items() if v == 2][0]
        for r in range(H):
            fours = [c for c in range(W) if g[r][c] == 4]
            if not fours:
                continue
            obj_lo, obj_hi = min(fours), max(fours)
            twos = [c for c in range(W) if g[r][c] == 2]
            bump = _profile_run(twos, line2)
            if line2 < line8:  # far edge on the left
                for c in range(0, obj_hi + 1):
                    if c < bump:
                        put(r, c, 2)
                    elif c < line8:
                        put(r, c, 8)
                    elif c < obj_lo:
                        put(r, c, 4)
                    else:
                        put(r, c, 3)
                put(r, line8, 8)
            else:  # far edge on the right
                for c in range(obj_lo, W):
                    if c <= obj_hi:
                        put(r, c, 3)
                    elif c < line8:
                        put(r, c, 4)
                    elif c >= W - bump:
                        put(r, c, 2)
                    else:
                        put(r, c, 8)
                put(r, line8, 8)
    else:
        line8 = [rr for rr, v in rows.items() if v == 8][0]
        line2 = [rr for rr, v in rows.items() if v == 2][0]
        for c in range(W):
            fours = [r for r in range(H) if g[r][c] == 4]
            if not fours:
                continue
            obj_lo, obj_hi = min(fours), max(fours)
            twos = [r for r in range(H) if g[r][c] == 2]
            bump = _profile_run(twos, line2)
            if line2 < line8:  # far edge at top
                for r in range(0, obj_hi + 1):
                    if r < bump:
                        put(r, c, 2)
                    elif r < line8:
                        put(r, c, 8)
                    elif r < obj_lo:
                        put(r, c, 4)
                    else:
                        put(r, c, 3)
                put(line8, c, 8)
            else:  # far edge at bottom
                for r in range(obj_lo, H):
                    if r <= obj_hi:
                        put(r, c, 3)
                    elif r < line8:
                        put(r, c, 4)
                    elif r >= H - bump:
                        put(r, c, 2)
                    else:
                        put(r, c, 8)
                put(line8, c, 8)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
