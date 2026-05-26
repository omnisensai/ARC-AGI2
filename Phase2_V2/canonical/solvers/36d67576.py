"""Canonical solver for ARC puzzle 36d67576.

Rule
----
Each grid contains several "objects": a skeleton drawn in color 4 with small
marker cells (colors 1, 2, 3) sitting around it. Exactly one object is the
*template*: it carries the full set of markers. Every other object is a partial
copy of the same 4-skeleton (possibly rotated / reflected) that carries only a
single anchor marker of color 2.

The transformation stamps the template's complete marker pattern onto every
partial object. For a partial object we find the dihedral transform (one of the
8 rotations/reflections) that maps the template's 4-skeleton onto the partial's
4-skeleton while keeping the color-2 anchor aligned; we then place every template
marker through that same transform.

Latent T is the mask of cells to overwrite together with the marker color to
write there: T = {(r, c): color}.
"""

from collections import deque

# The 8 dihedral transforms acting on (row, col) offsets.
_TRANSFORMS = [
    lambda r, c: (r, c),     # identity
    lambda r, c: (c, -r),    # rotate 90
    lambda r, c: (-r, -c),   # rotate 180
    lambda r, c: (-c, r),    # rotate 270
    lambda r, c: (r, -c),    # flip horizontal
    lambda r, c: (-r, c),    # flip vertical
    lambda r, c: (c, r),     # transpose
    lambda r, c: (-c, -r),   # anti-transpose
]


def _nonzero_components(g):
    """8-connected components of all non-zero cells."""
    H, W = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cur = []
                while q:
                    cr, cc = q.popleft()
                    cur.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W and
                                    g[nr][nc] != 0 and (nr, nc) not in seen):
                                seen.add((nr, nc))
                                q.append((nr, nc))
                comps.append(cur)
    return comps


def infer_T(input_grid):
    """Infer the latent overwrite mask {(r, c): color}."""
    g = input_grid
    H, W = len(g), len(g[0])

    # Split each non-zero component into its 4-skeleton and its markers (1/2/3).
    objs = []
    for comp in _nonzero_components(g):
        four = [(r, c) for r, c in comp if g[r][c] == 4]
        markers = {(r, c): g[r][c] for r, c in comp if g[r][c] in (1, 2, 3)}
        if four:
            objs.append((four, markers))

    if not objs:
        return {}

    # Template = the object carrying the most markers (the complete pattern).
    template = max(objs, key=lambda o: len(o[1]))
    tfour, tmarkers = template

    # Anchor of the template is its color-2 marker; everything is expressed
    # relative to that anchor so it can be re-placed on a partial's anchor.
    t_anchor = next((p for p, v in tmarkers.items() if v == 2), None)
    if t_anchor is None:
        return {}
    t4_rel = [(r - t_anchor[0], c - t_anchor[1]) for r, c in tfour]
    tmk_rel = [((r - t_anchor[0], c - t_anchor[1]), v)
               for (r, c), v in tmarkers.items()]

    T = {}
    for four, markers in objs:
        if (four, markers) == template:
            continue
        anchor = next((p for p, v in markers.items() if v == 2), None)
        if anchor is None:
            continue
        fset = set(four)

        # Find a dihedral transform mapping the template skeleton (anchored at
        # its 2) onto this object's skeleton (anchored at its 2).
        chosen = None
        for fn in _TRANSFORMS:
            placed = {(anchor[0] + fn(rr, cc)[0], anchor[1] + fn(rr, cc)[1])
                      for rr, cc in t4_rel}
            if placed == fset:
                chosen = fn
                break
        if chosen is None:
            continue

        # Stamp every template marker through that transform.
        for (rr, cc), color in tmk_rel:
            dr, dc = chosen(rr, cc)
            nr, nc = anchor[0] + dr, anchor[1] + dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
