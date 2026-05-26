def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(g):
    """8-connected components of non-zero cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                st = [(r, c)]
                cells = []
                while st:
                    y, x = st.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or seen[y][x] or g[y][x] == 0:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in nb:
                        st.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _colors(g, cells):
    d = {}
    for (y, x) in cells:
        d.setdefault(g[y][x], []).append((y, x))
    return d


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    Structure of the puzzle:
      * Exactly one KEY object: a component made of two colors with UNEQUAL
        counts. The rarer color is the single 'marker' (connector) cell; the
        other color forms an 'expand' pattern whose cell positions, taken
        relative to the marker, define a set of unit offsets (a stamp layout).
      * Several TARGET objects: components made of two EQUAL-sized rectangular
        blocks. One block's color matches the key's marker color (the anchor),
        the other is the body. For every key offset we stamp a copy of the body
        block, scaled by the block size, at offset*blocksize from the anchor's
        top-left. The original body block coincides with one of the offsets, so
        the targets get extended into the key's pattern, painted in the body's
        own color.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    comps = []
    for cells in _components(g):
        cols = _colors(g, cells)
        cc = {k: len(v) for k, v in cols.items()}
        comps.append((cells, cols, cc))

    # Find the KEY: two colors, unequal counts (prefer marker count == 1).
    key = None
    for entry in comps:
        cells, cols, cc = entry
        if len(cc) == 2:
            vals = sorted(cc.values())
            if vals[0] != vals[1]:
                key = entry
                if vals[0] == 1:
                    break
    if key is None:
        return {}

    kcells, kcols, kcc = key
    marker_color = min(kcc, key=kcc.get)
    expand_color = max(kcc, key=kcc.get)
    my, mx = kcols[marker_color][0]
    offsets = [(y - my, x - mx) for (y, x) in kcols[expand_color]]
    connector = marker_color

    T = {}
    for entry in comps:
        if entry is key:
            continue
        cells, cols, cc = entry
        if len(cc) != 2 or connector not in cols:
            continue
        body_color = [k for k in cc if k != connector][0]
        anchor = cols[connector]
        body = cols[body_color]

        ars = [y for y, x in anchor]
        acs = [x for y, x in anchor]
        ar0, ac0 = min(ars), min(acs)
        bh = max(ars) - ar0 + 1
        bw = max(acs) - ac0 + 1

        brs = [y for y, x in body]
        bcs = [x for y, x in body]
        br0, bc0 = min(brs), min(bcs)
        body_rel = [(y - br0, x - bc0) for (y, x) in body]

        for (oy, ox) in offsets:
            ty = ar0 + oy * bh
            tx = ac0 + ox * bw
            for (ry, rx) in body_rel:
                yy, xx = ty + ry, tx + rx
                if 0 <= yy < H and 0 <= xx < W:
                    T[(yy, xx)] = body_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
