"""Canonical solver for ARC puzzle 34cfa167.

Rule
----
The input contains a small decorated "template" anchored at one corner plus a
lone solid square "marker" somewhere else on the grid.

The template is built from a solid s*s anchor block of color ``c1`` together
with two strips that hang off it:
  * a horizontal strip (immediately right of the anchor, same rows), of the
    form ``[A, bg, B]`` -- the decorative period along the top/bottom edges.
  * a vertical strip (immediately below the anchor, same cols), of the form
    ``[C, bg, D]`` -- the decorative period along the left/right edges.

The lone marker is an identical s*s solid square of color ``c1`` that marks the
opposite corner of a rectangle.  The transformation stamps the four anchor
blocks at the rectangle's four corners, tiles the horizontal strip (unit =
``Hstrip + [bg]``) along the top and bottom edges, tiles the vertical strip
(unit = ``Vstrip + [bg]``) along the left and right edges, and draws four thin
border lines just outside those edges colored by the first element of the
respective strip (top/bottom = Hstrip[0], left/right = Vstrip[0]).

``infer_T`` reads all of this from the input alone and returns a latent mask as
a dict ``{(r, c): new_color}``; ``apply_T`` copies the input and overwrites only
the masked cells.
"""

from collections import Counter


def _bg_of(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def _clusters(g, bg):
    """Group non-bg cells into clusters, bridging small (<=2) gaps so the
    strip-with-gaps template stays one cluster while the far marker stays
    separate."""
    H, W = len(g), len(g[0])
    pts = set((r, c) for r in range(H) for c in range(W) if g[r][c] != bg)
    seen = set()
    out = []
    for p in list(pts):
        if p in seen:
            continue
        stack = [p]
        grp = []
        while stack:
            a, b = stack.pop()
            if (a, b) in seen or (a, b) not in pts:
                continue
            seen.add((a, b))
            grp.append((a, b))
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    if (dr, dc) != (0, 0):
                        stack.append((a + dr, b + dc))
        out.append(grp)
    return out


def _find_anchor_square(g, cellset, color, s):
    """Top-left of the first solid s*s monochrome square of `color`."""
    for (r, c) in sorted(cellset):
        if g[r][c] != color:
            continue
        ok = True
        for dr in range(s):
            for dc in range(s):
                if (r + dr, c + dc) not in cellset or g[r + dr][c + dc] != color:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return r, c
    return None


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _bg_of(g)

    cl = _clusters(g, bg)
    # marker cluster = smallest single-color cluster; template = richest cluster
    marker = None
    for grp in cl:
        if len(set(g[r][c] for r, c in grp)) == 1:
            if marker is None or len(grp) < len(marker):
                marker = grp
    template = None
    for grp in cl:
        if grp is marker:
            continue
        if template is None or len(set(g[r][c] for r, c in grp)) > len(
            set(g[r][c] for r, c in template)
        ):
            template = grp
    if marker is None or template is None:
        return {}

    c1 = Counter(g[r][c] for r, c in marker).most_common(1)[0][0]
    mrs = [r for r, c in marker]
    mcs = [c for r, c in marker]
    s = max(max(mrs) - min(mrs) + 1, max(mcs) - min(mcs) + 1)

    tset = set(template)
    anchor = _find_anchor_square(g, tset, c1, s)
    if anchor is None:
        return {}
    ar, ac = anchor

    # horizontal strip: columns immediately right of the anchor, in its rows
    maxc = ac + s - 1
    for (r, cc) in template:
        if ar <= r < ar + s and cc >= ac + s:
            maxc = max(maxc, cc)
    Hstrip = []
    for cc in range(ac + s, maxc + 1):
        nz = [g[r][cc] for r in range(ar, ar + s) if g[r][cc] != bg]
        Hstrip.append(nz[0] if nz else bg)

    # vertical strip: rows immediately below the anchor, in its columns
    maxr = ar + s - 1
    for (r, cc) in template:
        if ac <= cc < ac + s and r >= ar + s:
            maxr = max(maxr, r)
    Vstrip = []
    for rr in range(ar + s, maxr + 1):
        nz = [g[rr][c] for c in range(ac, ac + s) if g[rr][c] != bg]
        Vstrip.append(nz[0] if nz else bg)

    if not Hstrip or not Vstrip:
        return {}

    # opposite corner from the marker; normalize the rectangle corners
    mr, mc = min(mrs), min(mcs)
    r0, r1 = min(ar, mr), max(ar, mr)
    c0, c1c = min(ac, mc), max(ac, mc)

    T = {}

    def put(r, c, v):
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = v

    # four corner anchor blocks
    for (br, bc) in ((r0, c0), (r0, c1c), (r1, c0), (r1, c1c)):
        for dr in range(s):
            for dc in range(s):
                put(br + dr, bc + dc, c1)

    # tile horizontal strip along top and bottom edges
    hunit = Hstrip + [bg]
    for cc in range(c0 + s, c1c):
        v = hunit[(cc - (c0 + s)) % len(hunit)]
        for dr in range(s):
            put(r0 + dr, cc, v)
            put(r1 + dr, cc, v)

    # tile vertical strip along left and right edges
    vunit = Vstrip + [bg]
    for rr in range(r0 + s, r1):
        v = vunit[(rr - (r0 + s)) % len(vunit)]
        for dc in range(s):
            put(rr, c0 + dc, v)
            put(rr, c1c + dc, v)

    # thin border lines just outside the strips
    hb = Hstrip[0]
    for cc in range(c0 + s, c1c):
        put(r0 - 1, cc, hb)
        put(r1 + s, cc, hb)
    vb = Vstrip[0]
    for rr in range(r0 + s, r1):
        put(rr, c0 - 1, vb)
        put(rr, c1c + s, vb)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
