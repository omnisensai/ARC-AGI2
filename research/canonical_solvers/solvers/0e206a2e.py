"""Canonical solver for ARC puzzle 0e206a2e.

Rule
----
The grid contains one or more "template" objects: a connected blob built from a
common "filler" color (the most frequent non-background color) decorated with a
few rare "anchor" cells (the other colors). Scattered elsewhere are bare anchor
cells (the same rare colors, with no filler attached). Each scattered set of
anchors is the skeleton of a copy of a template: we find the template and the
dihedral orientation (rotation/reflection) whose anchor cells line up exactly,
in color and relative position, onto those bare anchor cells, then stamp the
whole oriented template there. Finally the original template objects are erased.

The latent transformation T is the mask of cells that change: the erased
template cells plus the stamped template copies.
"""

from collections import Counter


def _cells(g):
    H, W = len(g), len(g[0])
    return {(r, c): g[r][c] for r in range(H) for c in range(W) if g[r][c] != 0}


def _components(pts):
    """8-connected components of a set of points."""
    pts = set(pts)
    seen = set()
    comps = []
    for s in pts:
        if s in seen:
            continue
        stack = [s]
        comp = []
        while stack:
            r, c = stack.pop()
            if (r, c) in seen or (r, c) not in pts:
                continue
            seen.add((r, c))
            comp.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        comps.append(comp)
    return comps


def _orientations(shape):
    """All 8 dihedral variants of a {(r,c):color} shape, normalized to min 0."""
    def norm(s):
        r0 = min(r for r, c in s)
        c0 = min(c for r, c in s)
        return {(r - r0, c - c0): v for (r, c), v in s.items()}

    cur = dict(shape)
    results = []
    seen = set()
    for _ in range(2):                       # original + reflected
        s = cur
        for _ in range(4):                   # four rotations
            n = norm(s)
            key = frozenset(n.items())
            if key not in seen:
                seen.add(key)
                results.append(n)
            s = {(c, -r): v for (r, c), v in s.items()}   # rotate 90 deg
        cur = {(r, -c): v for (r, c), v in cur.items()}    # reflect
    return results


def infer_T(input_grid):
    """Compute the latent change mask {(r,c): new_color} from input structure."""
    H, W = len(input_grid), len(input_grid[0])
    inc = _cells(input_grid)
    if not inc:
        return {}

    counts = Counter(inc.values())
    filler = counts.most_common(1)[0][0]

    templates = []          # list of {(r,c): color} shapes containing filler
    bare = set()            # bare anchor cells (no filler in their component)
    for comp in _components(inc.keys()):
        if any(inc[x] == filler for x in comp):
            templates.append({(r, c): inc[(r, c)] for r, c in comp})
        else:
            bare.update(comp)

    T = {}
    # Erase the original template objects.
    for shape in templates:
        for (r, c) in shape:
            T[(r, c)] = 0

    # Stamp a copy of a template onto every set of bare anchors that matches
    # one of its dihedral orientations.
    for shape in templates:
        for variant in _orientations(shape):
            anchors = [(k, v) for k, v in variant.items() if v != filler]
            if not anchors:
                continue
            seed_pos, seed_col = anchors[0]
            for (br, bc) in sorted(bare):
                if inc[(br, bc)] != seed_col:
                    continue
                dr = br - seed_pos[0]
                dc = bc - seed_pos[1]
                placed = {(vr + dr, vc + dc): col for (vr, vc), col in variant.items()}
                anchor_cells = [(p, col) for p, col in placed.items() if col != filler]
                # every anchor of this orientation must land on a bare anchor
                # cell of the matching color.
                if all(p in bare and inc[p] == col for p, col in anchor_cells):
                    for (nr, nc), col in placed.items():
                        if 0 <= nr < H and 0 <= nc < W:
                            T[(nr, nc)] = col

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named by the mask T."""
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), col in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
