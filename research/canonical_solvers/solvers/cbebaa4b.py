"""Canonical latent-T solver for ARC puzzle cbebaa4b.

Rule (inferred from input structure alone):
The grid contains several disjoint objects ("shapes"). Each shape is a body of
a single color plus some color-2 "connector" markers sitting just outside the
body on the cells where it can dock to another shape. Exactly one shape is a
solid filled rectangle (height>1, width>1, every cell of its bbox filled) -- the
ANCHOR. The anchor stays fixed; every other shape is rigidly TRANSLATED (no
rotation/reflection) so that its connector markers coincide with matching
markers of an already-placed shape. Two markers may dock only when their
"outward" directions (away from their own body) are opposite (the bodies face
each other); at a corner an extra coinciding marker may be perpendicular. The
whole assembly grows as a tree out of the anchor. The output blanks every
originally non-zero cell and redraws each placed shape (body + markers) at its
docked position.

infer_T builds the docked-cell -> color mask; apply_T overwrites only those cells.
"""

from collections import deque


def _components(g):
    """8-connected components of all non-zero cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] != 0:
                                seen[ny][nx] = True
                                q.append((ny, nx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    # Parse shapes: body cells (color != 2), markers (color == 2), and the
    # outward direction of each marker (the direction pointing away from the
    # adjacent body cell).
    shapes = []
    for idx, cells in enumerate(_components(g)):
        bodyset = set((y, x) for y, x in cells if g[y][x] != 2)
        twos = [(y, x) for y, x in cells if g[y][x] == 2]
        if not bodyset:
            continue
        by0, bx0 = next(iter(bodyset))
        col = g[by0][bx0]
        outw = {}
        for (my, mx) in twos:
            od = None
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (my + dy, mx + dx) in bodyset:
                    od = (-dy, -dx)
                    break
            outw[(my, mx)] = od
        shapes.append({
            'id': idx, 'col': col, 'body': bodyset,
            'twos': twos, 'outw': outw, 'nm': len(twos),
        })

    # Anchor = largest solid filled rectangle (h>1, w>1).
    anchor = None
    best = -1
    for s in shapes:
        bset = s['body']
        ys = [y for y, x in bset]
        xs = [x for y, x in bset]
        h = max(ys) - min(ys) + 1
        w = max(xs) - min(xs) + 1
        if h > 1 and w > 1 and len(bset) == h * w and len(bset) > best:
            best = len(bset)
            anchor = s
    if anchor is None:
        return {}

    placed = {anchor['id']: (0, 0)}
    occ_bodies = set(anchor['body'])

    def pmark(s, tv):
        return {(y + tv[0], x + tv[1]): s['outw'][(y, x)] for (y, x) in s['twos']}

    def pbody(s, tv):
        return set((y + tv[0], x + tv[1]) for y, x in s['body'])

    def opp(a, b):
        return a is not None and b is not None and a[0] == -b[0] and a[1] == -b[1]

    def perp(a, b):
        return a is not None and b is not None and (a[0] * b[0] + a[1] * b[1]) == 0

    # Greedily grow the assembly tree out of the anchor.  Each step picks the
    # single best valid dock (most coinciding markers, then smallest shift).
    changed = True
    while changed:
        changed = False
        best_choice = None  # (sort_key, shape_id, translation, body_cells)
        for s in shapes:
            if s['id'] in placed:
                continue
            for pid, ptv in list(placed.items()):
                ps = next(x for x in shapes if x['id'] == pid)
                pm = pmark(ps, ptv)
                # Candidate translations: align one marker of s onto a placed
                # marker whose outward direction is exactly opposite.
                cand = set()
                for (ay, ax), aod in pm.items():
                    for (by, bx) in s['twos']:
                        bod = s['outw'][(by, bx)]
                        if opp(aod, bod):
                            cand.add((ay - by, ax - bx))
                for tv in cand:
                    sm = pmark(s, tv)
                    sb = pbody(s, tv)
                    coinc = [(c, sm[c], pm[c]) for c in sm if c in pm]
                    need = 2 if s['nm'] >= 2 else 1
                    if len(coinc) < need:
                        continue
                    # Every coinciding marker pair must be opposite or
                    # perpendicular (never the same direction), with at least
                    # one strictly opposite pair.
                    if any(not (opp(so, po) or perp(so, po)) for _, so, po in coinc):
                        continue
                    if not any(opp(so, po) for _, so, po in coinc):
                        continue
                    # Bodies may not overlap any already-placed body.
                    if sb & occ_bodies:
                        continue
                    key = (len(coinc), -abs(tv[0]) - abs(tv[1]))
                    if best_choice is None or key > best_choice[0]:
                        best_choice = (key, s['id'], tv, sb)
        if best_choice is not None:
            _, sid, tv, sb = best_choice
            placed[sid] = tv
            occ_bodies |= sb
            changed = True

    # Build the latent mask: blank every originally non-zero cell, then redraw
    # each placed shape (body color + its color-2 markers) at its docked spot.
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                T[(r, c)] = 0
    for s in shapes:
        if s['id'] not in placed:
            continue
        tv = placed[s['id']]
        for (y, x) in s['body']:
            ny, nx = y + tv[0], x + tv[1]
            if 0 <= ny < H and 0 <= nx < W:
                T[(ny, nx)] = s['col']
        for (y, x) in s['twos']:
            ny, nx = y + tv[0], x + tv[1]
            if 0 <= ny < H and 0 <= nx < W:
                T[(ny, nx)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
