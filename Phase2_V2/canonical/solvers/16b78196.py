"""Canonical solver for ARC puzzle 16b78196.

Rule (derived from input structure)
-----------------------------------
The grid contains one large solid "wall band" (the largest connected component)
plus several small free-floating shapes scattered around it. The wall band has a
number of carved "notches" -- dents reaching into one of its straight edges.

Exactly one free shape's protruding tip is congruent (same orientation, just
translated) to each genuine notch: that shape PLUGS the notch with its tip poking
into the wall, while the rest of its body sits just outside the wall edge. More
shapes then nest perpendicular to the wall, each interlocking with the previous
one (jagged edges complement so the union has no gaps), until the assembled
shapes tile a solid rectangular band flush against the wall edge. Shapes keep
their original orientation; they are only translated.

The transformation erases every original free shape and redraws them as these
nested stacks at the notches.

Latent-T form
-------------
`infer_T` derives, from the input alone, a mask `T = {(r,c): new_color}`:
  * original-shape cells -> 0   (erased)
  * assembled stack cells -> the shape's colour (drawn at the notch)
`apply_T` copies the input and overwrites only the masked cells.

The assembly is found by a backtracking packer:
  - locate the wall (largest component) and orient it horizontally;
  - for each candidate notch, try each unused shape as the plug (its tip must
    exactly equal the notch);
  - chain further shapes, each placed within the band's fixed column range,
    on the outer side of the wall, touching the current band, keeping every
    band column contiguous from the wall-adjacent row (the solidity invariant);
  - a stack is complete when its outer cells form a solid rectangle;
  - repeat until every shape has been consumed.
"""


def comps(g):
    """4-connected same-colour components of all non-zero cells."""
    H, W = len(g), len(g[0])
    seen = [[0] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                col = g[r][c]
                stk = [(r, c)]
                cells = []
                while stk:
                    a, b = stk.pop()
                    if a < 0 or b < 0 or a >= H or b >= W or seen[a][b] or g[a][b] != col:
                        continue
                    seen[a][b] = 1
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stk.append((a + dr, b + dc))
                out.append((col, cells))
    return out


def rot_cw(g, k):
    """Rotate a grid 90 degrees clockwise k times."""
    for _ in range(k % 4):
        H = len(g)
        g = [[g[H - 1 - r][c] for r in range(H)] for c in range(len(g[0]))]
    return g


def _norm(s):
    """Translate a set of cells so its bounding box starts at (0,0)."""
    rs = [r for r, c in s]
    cs = [c for r, c in s]
    r0, c0 = min(rs), min(cs)
    return frozenset((r - r0, c - c0) for r, c in s)


def _solve_horizontal(g):
    """Build the assembled output for a grid whose wall band is horizontal."""
    H, W = len(g), len(g[0])
    cs = comps(g)
    cs.sort(key=lambda x: -len(x[1]))
    wcells = cs[0][1]
    wset = set(wcells)
    rows = [c[0] for c in wcells]
    bt, bb = min(rows), max(rows)            # band top / bottom rows
    raw_shapes = [(col, frozenset(cells)) for col, cells in cs[1:]]
    norm_shapes = [(col, _norm(s)) for col, s in raw_shapes]
    n = len(norm_shapes)

    out = [row[:] for row in g]
    for _, s in raw_shapes:                  # erase original free shapes
        for (r, c) in s:
            out[r][c] = 0

    # candidate notches = connected background regions inside the wall band
    bg = set((r, c) for r in range(bt, bb + 1) for c in range(W) if g[r][c] == 0)
    rem = set(bg)
    clusters = []
    while rem:
        x = next(iter(rem))
        stk = [x]
        cl = set()
        while stk:
            y = stk.pop()
            if y not in rem:
                continue
            rem.discard(y)
            cl.add(y)
            r, c = y
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in rem:
                    stk.append((r + dr, c + dc))
        clusters.append(frozenset(cl))

    placement = {}            # (r,c) -> colour of assembled stacks
    used = [False] * n
    served = set()

    def free(pc):
        for (r, c) in pc:
            if not (0 <= r < H and 0 <= c < W):
                return False
            if (r, c) in placement or (r, c) in wset:
                return False
        return True

    def band_status(direction):
        """'complete' if the outer band cells form a solid rectangle, else 'growing'."""
        band = [(r, c) for (r, c) in placement
                if (r < bt if direction == 'up' else r > bb)]
        if not band:
            return 'growing'
        cmn = min(c for r, c in band)
        cmx = max(c for r, c in band)
        rmn = min(r for r, c in band)
        rmx = max(r for r, c in band)
        if len(band) == (rmx - rmn + 1) * (cmx - cmn + 1):
            return 'complete'
        return 'growing'

    def col_contig(direction):
        """Every band column's filled rows must be contiguous from the wall-adjacent row."""
        band = [(r, c) for (r, c) in placement
                if (r < bt if direction == 'up' else r > bb)]
        if not band:
            return True
        cols = {}
        for r, c in band:
            cols.setdefault(c, []).append(r)
        if direction == 'up':
            start = bt - 1
            for rws in cols.values():
                rws = sorted(rws)
                if rws[-1] != start or rws != list(range(rws[0], rws[-1] + 1)):
                    return False
        else:
            start = bb + 1
            for rws in cols.values():
                rws = sorted(rws)
                if rws[0] != start or rws != list(range(rws[0], rws[-1] + 1)):
                    return False
        return True

    def drop_candidates(s, dc, direction):
        """Yield every placement of shape s at column offset dc on the wall's outer side."""
        cells0 = [(r, c + dc) for r, c in s]
        if any(not (0 <= c < W) for r, c in cells0):
            return
        for dr in range(-H, H):
            pc = frozenset((r + dr, c) for r, c in cells0)
            if any(not (0 <= r < H) for r, c in pc):
                continue
            if direction == 'up':
                if any(r >= bt for r, c in pc):
                    continue
            else:
                if any(r <= bb for r, c in pc):
                    continue
            yield pc

    def chain(direction, on_complete):
        if band_status(direction) == 'complete':
            return on_complete()
        band0 = [(r, c) for (r, c) in placement
                 if (r < bt if direction == 'up' else r > bb)]
        bcmn = min(c for r, c in band0)
        bcmx = max(c for r, c in band0)
        for i in range(n):
            if used[i]:
                continue
            col, s = norm_shapes[i]
            lo = bcmn - max(c for r, c in s)
            hi = bcmx + 1
            for dc in range(lo, hi):
                for pc in drop_candidates(s, dc, direction):
                    if any(c < bcmn or c > bcmx for r, c in pc):
                        continue
                    if not free(pc):
                        continue
                    touch = False
                    for (r, c) in pc:
                        for dr2, dc2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            if (r + dr2, c + dc2) in placement:
                                touch = True
                                break
                        if touch:
                            break
                    if not touch:
                        continue
                    used[i] = True
                    for cc in pc:
                        placement[cc] = col
                    if col_contig(direction) and chain(direction, on_complete):
                        return True
                    used[i] = False
                    for cc in pc:
                        del placement[cc]
        return False

    def tip_offsets(s, notch):
        offs = set()
        for (sr, sc) in s:
            for (nr, nc) in notch:
                offs.add((nr - sr, nc - sc))
        return offs

    def serve(ci):
        """Try to plug cluster ci with some shape, then chain a complete stack."""
        notch = clusters[ci]
        for i in range(n):
            if used[i]:
                continue
            col, s = norm_shapes[i]
            for (dr, dc) in tip_offsets(s, notch):
                pc = frozenset((r + dr, c + dc) for r, c in s)
                if any(not (0 <= r < H and 0 <= c < W) for r, c in pc):
                    continue
                tip = frozenset((r, c) for r, c in pc if bt <= r <= bb)
                if tip != notch:
                    continue
                ub = [(r, c) for r, c in pc if r < bt]
                db = [(r, c) for r, c in pc if r > bb]
                if ub and not db:
                    direction = 'up'
                elif db and not ub:
                    direction = 'down'
                else:
                    continue
                body = ub if direction == 'up' else db
                if any(g[r][c] != 0 for r, c in body):
                    continue
                if not free(pc):
                    continue
                used[i] = True
                for cc in pc:
                    placement[cc] = col
                served.add(ci)
                if chain(direction, backtrack):
                    return True
                served.discard(ci)
                used[i] = False
                for cc in pc:
                    del placement[cc]
        return False

    def backtrack():
        if all(used):
            return True
        for ci in range(len(clusters)):
            if ci in served:
                continue
            if serve(ci):
                return True
        return all(used)

    backtrack()
    for (r, c), col in placement.items():
        out[r][c] = col
    return out


def infer_T(input_grid):
    """Infer the latent transformation mask T = {(r,c): new_color} from the input.

    The mask erases the original free shapes (-> 0) and draws the nested stacks
    assembled at the wall notches (-> shape colour). Computed entirely from the
    input's structure (largest component = wall, others = shapes).
    """
    g = input_grid
    H, W = len(g), len(g[0])
    cs = comps(g)
    if not cs:
        return {}
    cs.sort(key=lambda x: -len(x[1]))
    wcells = cs[0][1]
    rws = [c[0] for c in wcells]
    cls = [c[1] for c in wcells]
    horiz = (max(rws) - min(rws)) < (max(cls) - min(cls))

    if horiz:
        out = _solve_horizontal(g)
    else:
        # rotate so the wall is horizontal, solve, rotate the result back
        out = rot_cw(_solve_horizontal(rot_cw(g, 1)), 3)

    T = {}
    for r in range(H):
        for c in range(W):
            if out[r][c] != g[r][c]:
                T[(r, c)] = out[r][c]
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named by the mask T."""
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
