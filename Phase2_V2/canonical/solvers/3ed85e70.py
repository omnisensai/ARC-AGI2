def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(grid, region, bg):
    """8-connected components of non-bg cells restricted to `region` (a set of (r,c))."""
    rs = region
    seen = set()
    res = []
    for (r, c) in region:
        if grid[r][c] == bg or (r, c) in seen:
            continue
        stack = [(r, c)]
        comp = []
        while stack:
            a, b = stack.pop()
            if (a, b) in seen or (a, b) not in rs or grid[a][b] == bg:
                continue
            seen.add((a, b))
            comp.append((a, b))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((a + dr, b + dc))
        res.append(comp)
    return res


def _obj(grid, comp):
    r0 = min(r for r, c in comp)
    c0 = min(c for r, c in comp)
    cells = {(r - r0, c - c0): grid[r][c] for (r, c) in comp}
    h = max(r for r, c in comp) - r0 + 1
    w = max(c for r, c in comp) - c0 + 1
    return {'r0': r0, 'c0': c0, 'h': h, 'w': w, 'cells': cells}


def _split_legend(grid):
    """Split the grid into a legend region (background color 3) and a working
    region (background color 0), separated by a straight horizontal or vertical
    cut. Returns (legend_cells, working_cells) as sets of (r,c)."""
    H, W = len(grid), len(grid[0])

    def row_is_legend(r):
        cnt = {}
        for v in grid[r]:
            cnt[v] = cnt.get(v, 0) + 1
        return max(cnt, key=cnt.get) == 3

    def col_is_legend(c):
        cnt = {}
        for r in range(H):
            v = grid[r][c]
            cnt[v] = cnt.get(v, 0) + 1
        return max(cnt, key=cnt.get) == 3

    leg_rows = [row_is_legend(r) for r in range(H)]
    leg_cols = [col_is_legend(c) for c in range(W)]
    legend = set()
    working = set()
    if 0 < sum(leg_rows) < H:
        for r in range(H):
            for c in range(W):
                (legend if leg_rows[r] else working).add((r, c))
    elif 0 < sum(leg_cols) < W:
        for r in range(H):
            for c in range(W):
                (legend if leg_cols[c] else working).add((r, c))
    return legend, working


def _template_info(t):
    """Precompute per-color cell sets and bbox for a template object."""
    colorcells = {}
    for (rr, cc), v in t['cells'].items():
        colorcells.setdefault(v, set()).add((rr, cc))
    colorbbox = {}
    interior_only = {}  # color -> True if its region does not touch the template bbox edge
    for v, cl in colorcells.items():
        rs = [a for a, b in cl]
        cs = [b for a, b in cl]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        colorbbox[v] = (r0, c0, r1 - r0 + 1, c1 - c0 + 1)
        on_edge = any(a == 0 or a == t['h'] - 1 or b == 0 or b == t['w'] - 1 for a, b in cl)
        interior_only[v] = not on_edge
    return {'t': t, 'colorcells': colorcells, 'colorbbox': colorbbox,
            'interior': interior_only}


def _match_seed(s, tinfos):
    """Return (tinfo, gr0, gc0) where the template should be stamped with its
    cell (0,0) placed at grid (gr0, gc0). None if no match."""
    scells = s['cells']
    scolors = set(scells.values())

    # Type 1: multi-color corner fragment.  The seed is an exact sub-fragment of
    # a template, anchored so it covers one of the template's bbox corners.
    if len(scolors) > 1:
        for ti in tinfos:
            t = ti['t']
            tc = t['cells']
            if s['h'] > t['h'] or s['w'] > t['w']:
                continue
            corners = {(0, 0), (0, t['w'] - 1), (t['h'] - 1, 0), (t['h'] - 1, t['w'] - 1)}
            for dor in range(0, t['h'] - s['h'] + 1):
                for doc in range(0, t['w'] - s['w'] + 1):
                    if all(tc.get((rr + dor, cc + doc)) == v for (rr, cc), v in scells.items()):
                        covered = {(rr + dor, cc + doc) for (rr, cc) in scells}
                        if corners & covered:
                            return ti, s['r0'] - dor, s['c0'] - doc
        return None

    # Single-color seed.
    col = next(iter(scolors))
    is_solid = (len(scells) == s['h'] * s['w'])

    # Type 2: interior core.  The seed exactly equals a template color region
    # that is strictly interior (does not touch the template bbox edge).
    for ti in tinfos:
        if col not in ti['colorcells'] or not ti['interior'][col]:
            continue
        region = ti['colorcells'][col]
        rs = [a for a, b in region]
        cs = [b for a, b in region]
        r0, c0 = min(rs), min(cs)
        rel = {(a - r0, b - c0) for a, b in region}
        if rel == set(scells.keys()):
            return ti, s['r0'] - r0, s['c0'] - c0

    # Type 3: solid frame.  A solid block whose color spans the entire template
    # bbox -> stamp the full template over the seed's footprint.
    if is_solid:
        for ti in tinfos:
            t = ti['t']
            if col not in ti['colorbbox']:
                continue
            br, bc, bh, bw = ti['colorbbox'][col]
            if br == 0 and bc == 0 and bh == t['h'] and bw == t['w'] \
                    and bh == s['h'] and bw == s['w']:
                return ti, s['r0'], s['c0']
    return None


def infer_T(grid):
    H, W = len(grid), len(grid[0])
    legend, working = _split_legend(grid)
    Tmask = {}
    if not legend:
        return Tmask
    templates = [_obj(grid, c) for c in _components(grid, legend, 3)]
    seeds = [_obj(grid, c) for c in _components(grid, working, 0)]
    tinfos = [_template_info(t) for t in templates]

    for s in seeds:
        m = _match_seed(s, tinfos)
        if m is None:
            continue
        ti, gr0, gc0 = m
        for (rr, cc), v in ti['t']['cells'].items():
            gr, gc = gr0 + rr, gc0 + cc
            if 0 <= gr < H and 0 <= gc < W:
                Tmask[(gr, gc)] = v
    return Tmask


def apply_T(grid, Tmask):
    out = [row[:] for row in grid]
    for (r, c), v in Tmask.items():
        out[r][c] = v
    return out
