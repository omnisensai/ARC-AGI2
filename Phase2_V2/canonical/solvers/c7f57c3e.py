"""Canonical latent-T solver for ARC puzzle c7f57c3e.

Structure of the puzzle: the grid contains several "lollipop" objects on a
uniform background. Each object is built from a 1-coloured frame (a ring/cap)
with a coloured "head" block sitting in the frame interior and a coloured
"tail" block attached to one side (above or below the frame). Every object
belongs to one of exactly TWO decoration "types"; the two types share the same
frame geometry (up to a vertical flip) but differ in their head/tail colouring
and tail side, and each type may appear at several integer block-upscaled
sizes.

Transformation: every object is repainted as the OTHER type. We learn the base
(smallest) template of each type, and for each object render the partner type's
template upscaled to that object's frame size, aligned by the frame bounding
box. The latent mask records every cell whose colour changes.
"""

from collections import Counter


def bg_of(g):
    c = Counter()
    for row in g:
        for v in row:
            c[v] += 1
    return c.most_common(1)[0][0]


def _objects(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or a >= H or b < 0 or b >= W or seen[a][b] or g[a][b] == bg:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                objs.append(cells)
    return objs


def _obj_info(g, cells, bg):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    tile = [[bg] * w for _ in range(h)]
    for r, c in cells:
        tile[r - r0][c - c0] = g[r][c]
    ones = [(r, c) for r, c in cells if g[r][c] == 1]
    fr = [r for r, c in ones]
    fc = [c for r, c in ones]
    frame = (min(fr) - r0, min(fc) - c0, max(fr) - r0, max(fc) - c0)
    sig = frozenset(g[r][c] for r, c in cells if g[r][c] != 1)
    return dict(box=(r0, c0, r1, c1), tile=tile, frame=frame, sig=sig,
                fh=max(fr) - min(fr) + 1, fw=max(fc) - min(fc) + 1)


def _upscale(tile, s):
    return [[tile[r // s][c // s] for c in range(len(tile[0]) * s)]
            for r in range(len(tile) * s)]


def infer_T(input_grid):
    """Compute the latent transformation mask: {(r, c): new_color}."""
    g = input_grid
    H, W = len(g), len(g[0])
    bg = bg_of(g)
    objs = [_obj_info(g, o, bg) for o in _objects(g, bg)]

    # The two distinct decoration types (by their non-frame colour signature).
    sigs = []
    for o in objs:
        if o['sig'] not in sigs:
            sigs.append(o['sig'])

    T = {}
    if len(sigs) != 2:
        return dict(bg=bg, mask=T)

    # Base template per type = smallest object of that type.
    base = {}
    for s in sigs:
        members = [o for o in objs if o['sig'] == s]
        base[s] = min(members, key=lambda o: o['fh'])
    other = {sigs[0]: sigs[1], sigs[1]: sigs[0]}

    for o in objs:
        bt = base[other[o['sig']]]          # partner type's base template
        bf = bt['frame']
        base_fh = bf[2] - bf[0] + 1
        s = o['fh'] // base_fh              # integer upscale factor
        rt = _upscale(bt['tile'], s)        # rendered partner tile at this scale
        rf = (bf[0] * s, bf[1] * s, bf[2] * s + (s - 1), bf[3] * s + (s - 1))

        r0, c0, r1, c1 = o['box']
        ofr0, ofc0 = r0 + o['frame'][0], c0 + o['frame'][1]
        off_r = ofr0 - rf[0]                # align rendered frame to object frame
        off_c = ofc0 - rf[1]

        target = {}
        rh, rw = len(rt), len(rt[0])
        for rr in range(rh):
            for cc in range(rw):
                ar, ac = off_r + rr, off_c + cc
                if 0 <= ar < H and 0 <= ac < W:
                    target[(ar, ac)] = rt[rr][cc]
        # Clear any of this object's own cells not covered by the new rendering.
        for rr in range(r1 - r0 + 1):
            for cc in range(c1 - c0 + 1):
                ar, ac = r0 + rr, c0 + cc
                if (ar, ac) not in target and o['tile'][rr][cc] != bg:
                    target[(ar, ac)] = bg

        for (ar, ac), col in target.items():
            if 0 <= ar < H and 0 <= ac < W and g[ar][ac] != col:
                T[(ar, ac)] = col

    return dict(bg=bg, mask=T)


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), col in T['mask'].items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
