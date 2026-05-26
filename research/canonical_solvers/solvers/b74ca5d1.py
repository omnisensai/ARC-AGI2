"""Canonical latent-T solver for ARC puzzle b74ca5d1.

Rule (inferred from structure, no hardcoding):
  * Background = most common color.
  * The four grid corners, when non-background, are MARKERS carrying a color.
  * Every other figure is a small "shape": a cluster of cells made of one
    dominant MAIN color plus exactly one foreign SEED cell whose color equals a
    marker color.

  Latent transformation T (a mask {(r,c): new_color}):
    1. In-place swap. Inside each shape, the main-color cells take the seed
       color and the single seed cell takes the main color.
       Exception: when two shapes share a marker AND their bodies are exact
       transposes of one another, the swap must keep them transposes, so both
       seed cells take the SAME main color (that of the shape nearer the shared
       marker's corner).
    2. Corner stamps. For each marker color, take every shape whose seed equals
       that color, place each shape's full pattern at the marker's corner in its
       original orientation, and draw the union in the marker color (the cell
       coinciding with the marker stays the marker). When several shapes stamp
       into the same corner, a 1-wide straight dead-end limb of a shape that
       intrudes into a perpendicular gap of another shape is trimmed.

  apply_T copies the input and overwrites only the masked cells.
"""

import collections


def _bg(g):
    c = collections.Counter()
    for row in g:
        for v in row:
            c[v] += 1
    return c.most_common(1)[0][0]


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _cluster(cells, gap):
    parent = {p: p for p in cells}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    cs = set(cells)
    for (r, c) in cells:
        for dr in range(-gap, gap + 1):
            for dc in range(-gap, gap + 1):
                if (r + dr, c + dc) in cs:
                    parent[find((r, c))] = find((r + dr, c + dc))
    groups = collections.defaultdict(list)
    for p in cells:
        groups[find(p)].append(p)
    return list(groups.values())


def _segment(inp):
    """Return (bg, markers, corners, shapes).

    Each shape is dict: main, seed_color, seed_pos, cells(list), body(rel
    main-cells set), full(rel all-cells set), h, w, bbox(miny,minx,maxy,maxx).
    """
    bg = _bg(inp)
    H, W = len(inp), len(inp[0])
    corners = {(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)}
    markers = {inp[r][c] for (r, c) in corners if inp[r][c] != bg}

    cells = [(r, c) for r in range(H) for c in range(W)
             if (r, c) not in corners and inp[r][c] != bg]
    clusters = _cluster(cells, 2)

    seeded = []  # [cells_list, seed_pos]
    orphans = []
    for grp in clusters:
        seeds = [(r, c) for (r, c) in grp if inp[r][c] in markers]
        if len(seeds) == 1:
            seeded.append([list(grp), seeds[0]])
        elif len(seeds) == 0:
            orphans.append(grp)
        else:
            # rare: split, assign each non-seed cell to nearest seed
            buckets = {s: [s] for s in seeds}
            for (r, c) in grp:
                if (r, c) in seeds:
                    continue
                best = min(seeds, key=lambda s: _cheb((r, c), s))
                buckets[best].append((r, c))
            for s in seeds:
                seeded.append([buckets[s], s])
    for orph in orphans:
        best = None
        bd = 10 ** 9
        for i, (grp, seed) in enumerate(seeded):
            dmin = min(_cheb(o, gp) for o in orph for gp in grp)
            if dmin < bd:
                bd = dmin
                best = i
        if best is not None:
            seeded[best][0] = seeded[best][0] + list(orph)

    shapes = []
    for grp, seed in seeded:
        cnt = collections.Counter(inp[y][x] for (y, x) in grp
                                  if inp[y][x] not in markers)
        if not cnt:
            continue
        main = cnt.most_common(1)[0][0]
        ys = [y for y, x in grp]
        xs = [x for y, x in grp]
        miny, minx, maxy, maxx = min(ys), min(xs), max(ys), max(xs)
        body = frozenset((y - miny, x - minx) for (y, x) in grp
                         if inp[y][x] == main)
        full = frozenset((y - miny, x - minx) for (y, x) in grp)
        shapes.append({
            'main': main,
            'seed_color': inp[seed[0]][seed[1]],
            'seed_pos': seed,
            'cells': grp,
            'body': body,
            'full': full,
            'h': maxy - miny + 1,
            'w': maxx - minx + 1,
            'bbox': (miny, minx, maxy, maxx),
        })
    return bg, markers, corners, shapes


def _place(full, h, w, cr, cc, H, W):
    """Place shape's full pattern anchored at corner (cr,cc)."""
    out = set()
    for (r, c) in full:
        rr = r if cr == 0 else cr - (h - 1) + r
        ccc = c if cc == 0 else cc - (w - 1) + c
        if 0 <= rr < H and 0 <= ccc < W:
            out.add((rr, ccc))
    return out


def _stamp_drops(group):
    """group: list of (main, placed_cellset). Return cells to drop (trimmed
    1-wide dead-end limbs that intrude into another shape's perpendicular gap).
    """
    if len(group) < 2:
        return set()
    owner = collections.defaultdict(set)
    for m, cells in group:
        for cc in cells:
            owner[cc].add(m)

    def single(c):
        return len(owner.get(c, ())) == 1

    def occ_other(c, m):
        return c in owner and m not in owner[c]

    drops = set()
    for m, cells in group:
        cs = set(cells)

        def sdeg(x):
            return sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                       if (dr or dc) and (x[0] + dr, x[1] + dc) in cs)

        def wide_h(a):
            if a not in cs:
                return False
            cnt = 1
            y = a[1] - 1
            while (a[0], y) in cs:
                cnt += 1
                y -= 1
            y = a[1] + 1
            while (a[0], y) in cs:
                cnt += 1
                y += 1
            return cnt >= 3

        def wide_v(a):
            if a not in cs:
                return False
            cnt = 1
            x = a[0] - 1
            while (x, a[1]) in cs:
                cnt += 1
                x -= 1
            x = a[0] + 1
            while (x, a[1]) in cs:
                cnt += 1
                x += 1
            return cnt >= 3

        # vertical single-owner runs (perpendicular brackets are horizontal)
        for c0 in cs:
            r, c = c0
            if not single(c0):
                continue
            if (r - 1, c) in cs and single((r - 1, c)):
                continue
            run = []
            rr = r
            while (rr, c) in cs and single((rr, c)):
                run.append((rr, c))
                rr += 1
            if len(run) < 2:
                continue
            top, bot = run[0], run[-1]
            intr = any(occ_other((x[0], x[1] - 1), m) and
                       occ_other((x[0], x[1] + 1), m) for x in run)
            if not intr:
                continue
            if sdeg(bot) <= 1 and wide_h((top[0] - 1, c)):
                drops |= set(run)
            elif sdeg(top) <= 1 and wide_h((bot[0] + 1, c)):
                drops |= set(run)

        # horizontal single-owner runs (perpendicular brackets are vertical)
        for c0 in cs:
            r, c = c0
            if not single(c0):
                continue
            if (r, c - 1) in cs and single((r, c - 1)):
                continue
            run = []
            cc2 = c
            while (r, cc2) in cs and single((r, cc2)):
                run.append((r, cc2))
                cc2 += 1
            if len(run) < 2:
                continue
            left, right = run[0], run[-1]
            intr = any(occ_other((x[0] - 1, x[1]), m) and
                       occ_other((x[0] + 1, x[1]), m) for x in run)
            if not intr:
                continue
            if sdeg(right) <= 1 and wide_v((r, left[1] - 1)):
                drops |= set(run)
            elif sdeg(left) <= 1 and wide_v((r, right[1] + 1)):
                drops |= set(run)

    return {c for c in drops if single(c)}


def infer_T(input_grid):
    inp = input_grid
    H, W = len(inp), len(inp[0])
    bg, markers, corners, shapes = _segment(inp)

    T = {}

    # ---- 1. In-place swap (with transpose-pair exception) ----
    # Determine, per shape, the color its seed cell should adopt.
    seed_target = {}
    for i, s in enumerate(shapes):
        seed_target[i] = s['main']

    # Group shapes by shared marker (seed color) and detect transpose pairs.
    by_marker = collections.defaultdict(list)
    for i, s in enumerate(shapes):
        by_marker[s['seed_color']].append(i)

    def transpose(body):
        return frozenset((c, r) for (r, c) in body)

    for mc, idxs in by_marker.items():
        # find the marker's corner position(s)
        cps = [(cr, cc) for (cr, cc) in corners if inp[cr][cc] == mc]
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ia, ib = idxs[a], idxs[b]
                sa, sb = shapes[ia], shapes[ib]
                if sa['full'] == transpose(sb['full']):
                    # both seed cells take the main color of the shape nearer
                    # the shared marker's corner
                    def dist_to_corner(s):
                        miny, minx, maxy, maxx = s['bbox']
                        cy = (miny + maxy) / 2.0
                        cx = (minx + maxx) / 2.0
                        if not cps:
                            return cy + cx
                        return min(abs(cy - cr) + abs(cx - cc) for cr, cc in cps)
                    near = ia if dist_to_corner(sa) <= dist_to_corner(sb) else ib
                    seed_target[ia] = shapes[near]['main']
                    seed_target[ib] = shapes[near]['main']

    for i, s in enumerate(shapes):
        main = s['main']
        sc = s['seed_color']
        spos = s['seed_pos']
        for (y, x) in s['cells']:
            if (y, x) == spos:
                T[(y, x)] = seed_target[i]
            elif inp[y][x] == main:
                T[(y, x)] = sc
        # seed cell handled above

    # ---- 2. Corner stamps ----
    cornerlist = [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]
    for cr, cc in cornerlist:
        mc = inp[cr][cc]
        if mc == bg:
            continue
        group = []
        for s in shapes:
            if s['seed_color'] == mc:
                placed = _place(s['full'], s['h'], s['w'], cr, cc, H, W)
                group.append((s['main'], placed))
        if not group:
            continue
        union = set()
        for _, cells in group:
            union |= cells
        drops = _stamp_drops(group)
        for (r, c) in (union - drops):
            if (r, c) == (cr, cc):
                continue  # marker stays the marker
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
