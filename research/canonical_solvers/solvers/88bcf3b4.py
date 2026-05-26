"""Canonical latent-T solver for ARC puzzle 88bcf3b4.

Rule (per independent group in the grid):
  Each group consists of a long straight WALL line, a wavy SNAKE object that
  touches the wall, and a free MARKER object nearby.  The snake is re-drawn as a
  "ball" launched from its wall-contact cell.  The ball advances one step per
  move along the axis PARALLEL to the wall (exiting past the wall's end) and its
  PERPENDICULAR (lateral) component bounces: it hugs / wraps around the marker,
  then leaves mirrored.  The new snake has the same number of cells as the
  original (or fewer if it runs off the grid edge first).

infer_T builds a mask {(r,c): color}: marker/wall and unrelated cells untouched,
old snake cells reset to background, and the traced bouncing path painted in the
snake color.
"""

from collections import Counter


def _bg(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def _components(g, bg, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            color = g[r][c]
            st = [(r, c)]
            seen[r][c] = True
            cells = []
            while st:
                a, b = st.pop()
                cells.append((a, b))
                for da in (-1, 0, 1):
                    for db in (-1, 0, 1):
                        if da == 0 and db == 0:
                            continue
                        na, nb = a + da, b + db
                        if 0 <= na < H and 0 <= nb < W and not seen[na][nb] and g[na][nb] == color:
                            seen[na][nb] = True
                            st.append((na, nb))
            comps.append({'color': color, 'cells': cells, 'set': set(cells)})
    return comps


def _straight(cells):
    rs = {r for r, c in cells}
    cs = {c for r, c in cells}
    return len(rs) == 1 or len(cs) == 1


def _touch(a, b):
    for (r, c) in a:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in b:
                return True
    return False


def _next_lat(li, L, R, FL, F, FR):
    """Update the lateral component while hugging/bouncing off the marker.

    Neighbour booleans are taken relative to the current cell, oriented by the
    advance axis: L/R = marker on the lateral -1/+1 side, F = marker straight
    ahead, FL/FR = marker on the forward diagonal sides.
    """
    if (R and FR) or (L and FL):
        return 0
    if F:
        return li
    if R and not L:
        return 1
    if L and not R:
        return -1
    if li == 0 and (FL or FR):
        return 0
    return li


def _simulate(start, adv, lat, li0, M, H, W, maxlen):
    r, c = start
    path = [(r, c)]
    li = li0
    ar, ac = adv
    lr, lc = lat
    while len(path) < maxlen:
        def inM(a, b):
            return (r + a, c + b) in M
        L = inM(-lr, -lc)
        R = inM(lr, lc)
        F = inM(ar, ac)
        FL = inM(ar - lr, ac - lc)
        FR = inM(ar + lr, ac + lc)
        li = _next_lat(li, L, R, FL, F, FR)
        nr = r + ar + li * lr
        nc = c + ac + li * lc
        if not (0 <= nr < H and 0 <= nc < W):
            break
        r, c = nr, nc
        path.append((r, c))
    return path


def infer_T(input_grid):
    g = input_grid
    H = len(g)
    W = len(g[0])
    bg = _bg(g)
    comps = _components(g, bg, H, W)

    straights = [k for k in comps if _straight(k['cells']) and len(k['cells']) >= 4]

    # A snake is a non-straight object that touches a long straight line (its wall).
    snakes = []
    for k in comps:
        if _straight(k['cells']):
            continue
        wall = None
        for s in straights:
            if _touch(k['set'], s['set']):
                wall = s
                break
        if wall is not None:
            snakes.append((k, wall))

    snake_ids = {id(k) for k, _ in snakes}
    wall_ids = {id(w) for _, w in snakes}

    T = {}
    for snake, wall in snakes:
        scells = snake['cells']
        scolor = snake['color']
        wcells = wall['cells']
        wset = wall['set']
        wrs = {r for r, c in wcells}
        wcs = {c for r, c in wcells}
        vertical = (len(wcs) == 1)

        # snake start = snake cell orthogonally adjacent to the wall
        starts = [p for p in scells
                  if any((p[0] + dr, p[1] + dc) in wset
                         for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if not starts:
            continue

        if vertical:
            wcol = next(iter(wcs))
            rmin, rmax = min(wrs), max(wrs)
            start = starts[0]
            adv = (1 if abs(start[0] - rmax) <= abs(start[0] - rmin) else -1, 0)
            start = (max(starts, key=lambda s: s[0]) if adv[0] == 1
                     else min(starts, key=lambda s: s[0]))
            lat = (0, 1)
            open_sign = -1 if start[1] < wcol else 1
        else:
            wrow = next(iter(wrs))
            cmin, cmax = min(wcs), max(wcs)
            start = starts[0]
            adv = (0, 1 if abs(start[1] - cmax) <= abs(start[1] - cmin) else -1)
            start = (max(starts, key=lambda s: s[1]) if adv[1] == 1
                     else min(starts, key=lambda s: s[1]))
            lat = (1, 0)
            open_sign = -1 if start[0] < wrow else 1

        # marker = nearest free object (neither a snake nor a snake's wall)
        scen = (sum(p[0] for p in scells) / len(scells),
                sum(p[1] for p in scells) / len(scells))
        marker = None
        best = 1e18
        for k in comps:
            if id(k) in snake_ids or id(k) in wall_ids:
                continue
            kc = (sum(p[0] for p in k['cells']) / len(k['cells']),
                  sum(p[1] for p in k['cells']) / len(k['cells']))
            dd = abs(kc[0] - scen[0]) + abs(kc[1] - scen[1])
            if dd < best:
                best = dd
                marker = k
        Mset = marker['set'] if marker else set()

        # initial lateral: head into open space unless the marker lies strictly
        # on the wall side (then advance straight and meet it later).
        if marker is None:
            li0 = open_sign
        else:
            mcen = (sum(p[0] for p in marker['cells']) / len(marker['cells']),
                    sum(p[1] for p in marker['cells']) / len(marker['cells']))
            if lat == (0, 1):
                want = 1 if mcen[1] > start[1] else (-1 if mcen[1] < start[1] else 0)
            else:
                want = 1 if mcen[0] > start[0] else (-1 if mcen[0] < start[0] else 0)
            li0 = 0 if want == -open_sign else open_sign

        maxlen = len(scells)
        path = _simulate(start, adv, lat, li0, Mset, H, W, maxlen)
        pset = set(path)
        for p in scells:
            if p not in pset:
                T[p] = bg
        for p in path:
            T[p] = scolor
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
