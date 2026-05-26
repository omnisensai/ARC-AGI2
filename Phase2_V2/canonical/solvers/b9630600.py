def _boxes(g):
    """Find axis-aligned hollow rectangles (color 3) as bounding boxes."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 3 and not seen[r][c]:
                st = [(r, c)]
                cells = []
                while st:
                    y, x = st.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or seen[y][x] or g[y][x] != 3:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        st.append((y + dy, x + dx))
                ys = [y for y, x in cells]
                xs = [x for y, x in cells]
                res.append((min(ys), max(ys), min(xs), max(xs)))
    return sorted(res)


def infer_T(input_grid):
    """Connect aligned boxes with hollow tubes (mask of added/opened cells).

    Boxes that share a center row (H) or center column (V) and are mutual
    nearest neighbours are candidate connections; an MST over the inter-box
    gaps selects the actual connections.  Each connection draws a tube whose
    total cross-section equals the smaller box's perpendicular interior; the
    two outer cells are walls and the inner (cross - 2) cells form a hollow
    passage cut through both box walls.  When cross-section <= 2 there is no
    hollow interior and the bridge is drawn solid.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    bx = _boxes(g)
    n = len(bx)
    cy = [(r0 + r1) / 2.0 for r0, r1, c0, c1 in bx]
    cx = [(c0 + c1) / 2.0 for r0, r1, c0, c1 in bx]

    def nearest_dir(i, axis, sign):
        best = None
        bd = 1e9
        for j in range(n):
            if j == i:
                continue
            if axis == 'H' and abs(cy[i] - cy[j]) > 1e-9:
                continue
            if axis == 'V' and abs(cx[i] - cx[j]) > 1e-9:
                continue
            d = (cx[j] - cx[i]) if axis == 'H' else (cy[j] - cy[i])
            if sign * d <= 0:
                continue
            if abs(d) < bd:
                bd = abs(d)
                best = j
        return best

    cand = []
    seen_e = set()
    for i in range(n):
        for axis in ('H', 'V'):
            for sign in (1, -1):
                j = nearest_dir(i, axis, sign)
                if j is not None and nearest_dir(j, axis, -sign) == i:
                    e = tuple(sorted((i, j)))
                    if e in seen_e:
                        continue
                    seen_e.add(e)
                    a, b = e
                    if axis == 'H':
                        gap = max(bx[a][2], bx[b][2]) - min(bx[a][3], bx[b][3]) - 1
                    else:
                        gap = max(bx[a][0], bx[b][0]) - min(bx[a][1], bx[b][1]) - 1
                    cand.append((gap, a, b, axis))
    cand.sort()

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = []
    for gap, a, b, axis in cand:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            edges.append((a, b, axis))

    T = {}

    def set_cell(r, c, v):
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = v

    for a, b, axis in edges:
        ra0, ra1, ca0, ca1 = bx[a]
        rb0, rb1, cb0, cb1 = bx[b]
        if axis == 'H':
            if ca1 < cb0:
                L, R = (ra0, ra1, ca0, ca1), (rb0, rb1, cb0, cb1)
            else:
                L, R = (rb0, rb1, cb0, cb1), (ra0, ra1, ca0, ca1)
            lr0, lr1, lc0, lc1 = L
            rr0, rr1, rc0, rc1 = R
            ih_L = lr1 - lr0 - 1
            ih_R = rr1 - rr0 - 1
            total = min(ih_L, ih_R)
            ctr = (lr0 + lr1) / 2.0 if ih_L <= ih_R else (rr0 + rr1) / 2.0
            t0 = int(round(ctr - (total - 1) / 2.0))
            t1 = t0 + total - 1
            gap_cols = range(lc1 + 1, rc0)
            inner_rows = range(t0 + 1, t1)
            if total <= 2:
                for r in range(t0, t1 + 1):
                    for c in gap_cols:
                        set_cell(r, c, 3)
            else:
                for c in gap_cols:
                    set_cell(t0, c, 3)
                    set_cell(t1, c, 3)
                for r in inner_rows:
                    set_cell(r, lc1, 0)
                    set_cell(r, rc0, 0)
        else:
            if ra1 < rb0:
                Tp, Bt = (ra0, ra1, ca0, ca1), (rb0, rb1, cb0, cb1)
            else:
                Tp, Bt = (rb0, rb1, cb0, cb1), (ra0, ra1, ca0, ca1)
            tr0, tr1, tc0, tc1 = Tp
            br0, br1, bc0, bc1 = Bt
            iw_T = tc1 - tc0 - 1
            iw_B = bc1 - bc0 - 1
            total = min(iw_T, iw_B)
            ctr = (tc0 + tc1) / 2.0 if iw_T <= iw_B else (bc0 + bc1) / 2.0
            t0 = int(round(ctr - (total - 1) / 2.0))
            t1 = t0 + total - 1
            gap_rows = range(tr1 + 1, br0)
            inner_cols = range(t0 + 1, t1)
            if total <= 2:
                for r in gap_rows:
                    for c in range(t0, t1 + 1):
                        set_cell(r, c, 3)
            else:
                for r in gap_rows:
                    set_cell(r, t0, 3)
                    set_cell(r, t1, 3)
                for c in inner_cols:
                    set_cell(tr1, c, 0)
                    set_cell(br0, c, 0)
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
