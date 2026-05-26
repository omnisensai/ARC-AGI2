"""Canonical latent-T solver for ARC puzzle 3e6067c3.

Rule (same-size grid):
  - The grid contains square "boxes" (a solid square region with a single
    minority-colored center marker) plus a one-row "legend" of isolated single
    colored cells near the bottom.
  - The legend lists colors in order, forming a PATH through the boxes:
    legend[0] -> legend[1] -> legend[2] -> ...  Each color identifies a box by
    its center marker color.
  - For every consecutive pair (A, B) in the legend we draw an arrow/ray from
    box A toward the adjacent, axis-aligned box B (same center-row band for a
    horizontal step, same center-column band for a vertical step), filling the
    background gap between the two boxes' bounding squares with color A, across
    the band spanned by A's center marker.
  - The path is followed deterministically: the source of step i is the box we
    arrived at in step i-1, so duplicate center colors are disambiguated.

infer_T computes the set of (cell -> color) overwrites from the input alone;
apply_T copies the input and paints only those cells.
"""

from collections import Counter


def _bg(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def _components(g, bg):
    """4-connected components of non-background cells."""
    H = len(g); W = len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]; cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or seen[y][x] or g[y][x] == bg:
                        continue
                    seen[y][x] = True; cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _parse(g):
    """Return (bg, boxes, legend).

    box = dict with bounding box (r0,r1,c0,c1), center color `col`, and the
    bounding band of its center marker cells (cr0,cr1,cc0,cc1).
    legend = list of colors in column order from the densest single-cell row.
    """
    bg = _bg(g)
    comps = _components(g, bg)
    boxes = []
    rowgroups = {}
    for cells in comps:
        rs = [y for y, x in cells]; cs = [x for y, x in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        h = r1 - r0 + 1; w = c1 - c0 + 1
        if h >= 3 and w >= 3 and len(cells) >= 8:
            colcnt = Counter(g[y][x] for y, x in cells)
            ctr = min(colcnt, key=lambda k: colcnt[k])  # minority = center marker
            ccells = [(y, x) for y, x in cells if g[y][x] == ctr]
            crs = [y for y, x in ccells]; ccs = [x for y, x in ccells]
            boxes.append(dict(r0=r0, r1=r1, c0=c0, c1=c1, col=ctr,
                              cr0=min(crs), cr1=max(crs),
                              cc0=min(ccs), cc1=max(ccs)))
        elif len(cells) == 1:
            rowgroups.setdefault(rs[0], []).append((cs[0], g[rs[0]][cs[0]]))
    legend = []
    if rowgroups:
        lr = max(rowgroups, key=lambda r: len(rowgroups[r]))
        legend = [col for c, col in sorted(rowgroups[lr])]
    return bg, boxes, legend


def _connect(g, bg, A, B):
    """If boxes A and B are axis-aligned and separated only by background,
    return (orientation, gap_range, band); else None."""
    # horizontal: same center-row band
    if A['cr0'] == B['cr0'] and A['cr1'] == B['cr1']:
        band = (A['cr0'], A['cr1'])
        if B['c0'] > A['c1']:
            rng = (A['c1'] + 1, B['c0'] - 1)
        elif B['c1'] < A['c0']:
            rng = (B['c1'] + 1, A['c0'] - 1)
        else:
            return None
        for x in range(rng[0], rng[1] + 1):
            for y in range(band[0], band[1] + 1):
                if g[y][x] != bg:
                    return None
        return ('H', rng, band)
    # vertical: same center-column band
    if A['cc0'] == B['cc0'] and A['cc1'] == B['cc1']:
        band = (A['cc0'], A['cc1'])
        if B['r0'] > A['r1']:
            rng = (A['r1'] + 1, B['r0'] - 1)
        elif B['r1'] < A['r0']:
            rng = (B['r1'] + 1, A['r0'] - 1)
        else:
            return None
        for y in range(rng[0], rng[1] + 1):
            for x in range(band[0], band[1] + 1):
                if g[y][x] != bg:
                    return None
        return ('V', rng, band)
    return None


def infer_T(input_grid):
    """Compute the latent transformation mask: dict {(r, c): new_color}."""
    g = input_grid
    bg, boxes, legend = _parse(g)
    T = {}
    if len(legend) < 2:
        return T

    # Find the starting box: a box of color legend[0] that connects to a box of
    # color legend[1] (disambiguates duplicate center colors).
    cur = None
    for ba in boxes:
        if ba['col'] != legend[0]:
            continue
        for bb in boxes:
            if bb is ba or bb['col'] != legend[1]:
                continue
            if _connect(g, bg, ba, bb):
                cur = ba
                break
        if cur is not None:
            break
    if cur is None:
        return T

    visited = {id(cur)}
    for i in range(len(legend) - 1):
        A = legend[i]; B = legend[i + 1]
        nxt = None; conn = None
        for bb in boxes:
            if bb is cur or bb['col'] != B:
                continue
            c = _connect(g, bg, cur, bb)
            if c:
                if id(bb) not in visited:  # prefer an unvisited target
                    nxt = bb; conn = c
                    break
                if nxt is None:
                    nxt = bb; conn = c
        if nxt is None:
            break
        ori, rng, band = conn
        if ori == 'H':
            for x in range(rng[0], rng[1] + 1):
                for y in range(band[0], band[1] + 1):
                    T[(y, x)] = A
        else:
            for y in range(rng[0], rng[1] + 1):
                for x in range(band[0], band[1] + 1):
                    T[(y, x)] = A
        cur = nxt
        visited.add(id(cur))
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
