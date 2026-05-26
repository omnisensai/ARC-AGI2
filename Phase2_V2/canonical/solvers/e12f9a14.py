"""Canonical latent-T solver for ARC puzzle e12f9a14.

Structure of the task
---------------------
The grid contains several small 4x4 "boxes": a one-cell-thick frame (border
color) enclosing a 2x2 block of a fill color, drawn on a uniform background.
Some perimeter cells of each frame are missing (replaced by background); these
are "gaps".  Each gap emits a ray of that box's fill color travelling outward:

  * an edge-mid gap emits a straight ray perpendicular to that edge,
  * a corner gap emits a 45-degree diagonal ray away from the box.

Rays interact: when two rays of different boxes cross, they bond and continue
together as an adjacent parallel pair, moving in the (clamped) vector sum of
their headings.  A diagonal+straight bond yields a 2:1 staircase, a
right+up bond yields a clean diagonal, two converging diagonals yield a
straight (vertical/horizontal) corridor, etc.  Bonds cascade.

`infer_T` runs this ray simulation purely from the input structure and returns
a mask {(r,c): color} of cells to paint.  `apply_T` overwrites only those
background cells.
"""


def _bg_of(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_boxes(g):
    """Detect 4x4 frames (possibly truncated at the grid edge) by locating
    their 2x2 fill blocks."""
    H, W = len(g), len(g[0])
    bg = _bg_of(g)
    boxes = {}
    for r in range(H - 1):
        for c in range(W - 1):
            f = g[r][c]
            if f == bg:
                continue
            if not (g[r][c + 1] == f and g[r + 1][c] == f and g[r + 1][c + 1] == f):
                continue
            br, bc = r - 1, c - 1  # frame top-left
            nb = []
            for rr in range(br, br + 4):
                for cc in range(bc, bc + 4):
                    if 0 <= rr < H and 0 <= cc < W:
                        v = g[rr][cc]
                        if v != bg and v != f:
                            nb.append(v)
            if not nb:
                continue
            bc_counts = {}
            for v in nb:
                bc_counts[v] = bc_counts.get(v, 0) + 1
            border = max(bc_counts, key=bc_counts.get)
            boxes[(br, bc)] = {'tl': (br, bc), 'fill': f, 'border': border}
    return list(boxes.values()), bg


def _gaps_of(g, b):
    """Return (gaps, gap_label_set). Each gap is ((r,c), dir, label)."""
    br, bc = b['tl']
    bg = _bg_of(g)
    H, W = len(g), len(g[0])
    cells = {
        (br, bc): (-1, -1), (br, bc + 3): (-1, 1),
        (br + 3, bc): (1, -1), (br + 3, bc + 3): (1, 1),
        (br, bc + 1): (-1, 0), (br, bc + 2): (-1, 0),
        (br + 3, bc + 1): (1, 0), (br + 3, bc + 2): (1, 0),
        (br + 1, bc): (0, -1), (br + 2, bc): (0, -1),
        (br + 1, bc + 3): (0, 1), (br + 2, bc + 3): (0, 1),
    }
    lab = {
        (br, bc): 'TL', (br, bc + 3): 'TR', (br + 3, bc): 'BL', (br + 3, bc + 3): 'BR',
        (br, bc + 1): 'T1', (br, bc + 2): 'T2', (br + 3, bc + 1): 'B1', (br + 3, bc + 2): 'B2',
        (br + 1, bc): 'L1', (br + 2, bc): 'L2', (br + 1, bc + 3): 'R1', (br + 2, bc + 3): 'R2',
    }
    gl = set()
    res = []
    for (pr, pc), dr in cells.items():
        if 0 <= pr < H and 0 <= pc < W and g[pr][pc] == bg:
            gl.add(lab[(pr, pc)])
            res.append(((pr, pc), dr, lab[(pr, pc)]))
    return res, gl


def _sg(x):
    return (x > 0) - (x < 0)


def _step_cell(pos, v, err):
    """One Bresenham step of a ray with (possibly non-unit) velocity v."""
    vy, vx = v
    ay, ax = abs(vy), abs(vx)
    sy, sx = _sg(vy), _sg(vx)
    r, c = pos
    if ay == 0:
        return (r, c + sx), err
    if ax == 0:
        return (r + sy, c), err
    if ay >= ax:
        r += sy
        err += ax
        if 2 * err >= ay:
            c += sx
            err -= ay
        return (r, c), err
    else:
        c += sx
        err += ay
        if 2 * err >= ax:
            r += sy
            err -= ax
        return (r, c), err


def _phase_of(nv):
    ay, ax = abs(nv[0]), abs(nv[1])
    prim, sec = max(ay, ax), min(ay, ax)
    return -(prim - sec)


def _trace_ray(ray, H, W, blocked):
    cells = [ray['start']]
    p = ray['start']
    v = ray['v0']
    err = 0
    bends = ray['bends']
    if p in bends:
        v, err = bends[p]
    for _ in range(2 * (H + W) + 5):
        np_, nerr = _step_cell(p, v, err)
        if not (0 <= np_[0] < H and 0 <= np_[1] < W) or np_ in blocked:
            break
        cells.append(np_)
        p, err = np_, nerr
        if p in bends:
            v, err = bends[p]
    return cells


def _vel_at(ray, cell, H, W, blocked):
    p = ray['start']
    v = ray['v0']
    err = 0
    bends = ray['bends']
    if p in bends:
        v, err = bends[p]
    if p == cell:
        return v
    for _ in range(2 * (H + W) + 5):
        np_, nerr = _step_cell(p, v, err)
        if not (0 <= np_[0] < H and 0 <= np_[1] < W) or np_ in blocked:
            return v
        p, err = np_, nerr
        if p in bends:
            v, err = bends[p]
        if p == cell:
            return v
    return v


# A corner gap is "decorative" (emits no ray) when the box's gaps form a
# chiral pinwheel of one corner plus two specific edge-mid cells.
_SUPPRESS = {
    'BR': [{'L1', 'T2'}],
    'TL': [{'B1', 'R2'}],
    'BL': [{'R1', 'T1'}],
    'TR': [{'B2', 'L2'}],
}


def _corner_suppressed(label, gl):
    for need in _SUPPRESS.get(label, []):
        if need <= gl:
            return True
    return False


def infer_T(input_grid):
    """Compute the latent transformation: simulate all rays and return the set
    of cells they paint as {(r, c): color}."""
    inp = input_grid
    H, W = len(inp), len(inp[0])
    boxes, bg = _find_boxes(inp)
    blocked = set((r, c) for r in range(H) for c in range(W) if inp[r][c] != bg)

    rays = []
    for b in boxes:
        gs, gl = _gaps_of(inp, b)
        for (gr, gc), dr, label in gs:
            if label in ('TL', 'TR', 'BL', 'BR') and _corner_suppressed(label, gl):
                continue
            rays.append({'start': (gr, gc), 'v0': dr, 'color': b['fill'], 'bends': {}})

    n = len(rays)
    resolved = set()
    for _iter in range(4000):
        paths = [_trace_ray(r, H, W, blocked) for r in rays]
        idx = [{cell: k for k, cell in enumerate(p)} for p in paths]
        best = None
        for i in range(n):
            for j in range(i + 1, n):
                if rays[i]['color'] == rays[j]['color']:
                    continue
                pi, pj = paths[i], paths[j]
                # perpendicular crossing: a shared cell
                for X in (set(pi) & set(pj)):
                    k = idx[i][X]
                    m = idx[j][X]
                    if k == 0 or m == 0:
                        continue
                    dist = k + m
                    if best is None or dist < best[0]:
                        best = (dist, i, j, 'perp', X, k, m)
                # diagonal interleave (swap) crossing
                for k in range(len(pi) - 1):
                    A = pi[k]
                    A2 = pi[k + 1]
                    if A2[0] - A[0] == 0 or A2[1] - A[1] == 0:
                        continue
                    cand1 = (A[0], A2[1])
                    cand2 = (A2[0], A[1])
                    if cand1 in idx[j] and cand2 in idx[j]:
                        m1 = idx[j][cand1]
                        m2 = idx[j][cand2]
                        if m2 == m1 + 1:
                            dist = k + m1
                            if best is None or dist < best[0]:
                                best = (dist, i, j, 'inter', (A, A2, cand1, cand2), k, m1)
        if best is None:
            break
        dist, i, j, typ, info, k, m = best
        if typ == 'perp':
            bi = paths[i][k - 1]
            bj = paths[j][m - 1]
        else:
            A, A2, cand1, cand2 = info
            bi = A
            bj = cand1
        key = (i, bi, j, bj)
        if key in resolved:
            break
        resolved.add(key)
        vi = _vel_at(rays[i], bi, H, W, blocked)
        vj = _vel_at(rays[j], bj, H, W, blocked)
        # already-parallel rays form a travelling bundle; do not re-bond them
        if (_sg(vi[0]), _sg(vi[1])) == (_sg(vj[0]), _sg(vj[1])):
            continue
        nv = (_sg(vi[0]) + _sg(vj[0]), _sg(vi[1]) + _sg(vj[1]))
        if nv == (0, 0):
            continue
        ph = _phase_of(nv)
        rays[i]['bends'][bi] = (nv, ph)
        rays[j]['bends'][bj] = (nv, ph)

        # Bundle propagation: a parallel-adjacent partner of a deflected ray
        # follows it (the whole travelling pair/corridor turns together).
        for who, bcell, prev in ((i, bi, vi), (j, bj, vj)):
            udir = (_sg(prev[0]), _sg(prev[1]))
            if udir[0] == 0 and udir[1] == 0:
                continue
            # perpendicular offsets to the travel direction
            if udir[0] == 0 or udir[1] == 0:
                perps = [(udir[1], udir[0]), (-udir[1], -udir[0])]
            else:
                perps = [(udir[0], -udir[1]), (-udir[0], udir[1])]
            for off in perps:
                pcell = (bcell[0] + off[0], bcell[1] + off[1])
                for j2 in range(n):
                    if j2 == who or rays[j2]['color'] == rays[who]['color']:
                        continue
                    if pcell in rays[j2]['bends']:
                        continue
                    p2 = _trace_ray(rays[j2], H, W, blocked)
                    if pcell not in p2:
                        continue
                    v2 = _vel_at(rays[j2], pcell, H, W, blocked)
                    if (_sg(v2[0]), _sg(v2[1])) == udir:
                        rays[j2]['bends'][pcell] = (nv, ph)

    T = {}
    for r in rays:
        for cell in _trace_ray(r, H, W, blocked):
            if cell not in T:
                T[cell] = r['color']
    return T, bg


def apply_T(input_grid, T):
    Tmask, bg = T
    out = [row[:] for row in input_grid]
    for (r, c), col in Tmask.items():
        if out[r][c] == bg:
            out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
