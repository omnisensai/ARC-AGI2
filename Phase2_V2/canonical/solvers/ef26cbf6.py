def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    # separator color = the color forming full rows/cols
    sep_rows = [r for r in range(H) if len(set(g[r])) == 1]
    if sep_rows:
        sep = g[sep_rows[0]][0]
    else:
        sep = 4
    sep_rows = [r for r in range(H) if all(g[r][c] == sep for c in range(W))]
    sep_cols = [c for c in range(W) if all(g[r][c] == sep for r in range(H))]

    # panel boundaries
    row_bounds = []
    prev = 0
    for r in sep_rows + [H]:
        if r > prev:
            row_bounds.append((prev, r))
        prev = r + 1
    col_bounds = []
    prev = 0
    for c in sep_cols + [W]:
        if c > prev:
            col_bounds.append((prev, c))
        prev = c + 1

    # classify each panel: pattern (contains 1s), or marker (single other color)
    panels = {}  # (pi,pj) -> dict
    for pi, (r0, r1) in enumerate(row_bounds):
        for pj, (c0, c1) in enumerate(col_bounds):
            cells = {}
            for r in range(r0, r1):
                for c in range(c0, c1):
                    v = g[r][c]
                    if v != 0 and v != sep:
                        cells.setdefault(v, []).append((r, c))
            panels[(pi, pj)] = {'box': (r0, r1, c0, c1), 'cells': cells}

    def is_pattern(p):
        return 1 in p['cells']

    def marker_color(p):
        for col in p['cells']:
            if col != 1:
                return col
        return None

    # Build mapping from pattern panel -> marker color via shared axis.
    # Markers occupy panels along one axis; patterns the other.
    T = {}
    for key, p in panels.items():
        if not is_pattern(p):
            continue
        pi, pj = key
        # find marker panel sharing same row-index or same col-index
        mc = None
        # prefer same column (marker above/below), then same row
        for (qi, qj), q in panels.items():
            if (qi, qj) == key or is_pattern(q):
                continue
            m = marker_color(q)
            if m is None:
                continue
            if qj == pj:
                mc = m
                break
        if mc is None:
            for (qi, qj), q in panels.items():
                if (qi, qj) == key or is_pattern(q):
                    continue
                m = marker_color(q)
                if m is None:
                    continue
                if qi == pi:
                    mc = m
                    break
        if mc is None:
            continue
        for (r, c) in p['cells'][1]:
            T[(r, c)] = mc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
