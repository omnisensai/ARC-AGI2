"""Canonical solver for ARC puzzle 1da012fc.

Rule
----
The grid contains a "legend": a solid rectangle of color 5 with a few colored
marker cells embedded inside it. Scattered elsewhere are several outlined
shapes, all drawn in a single base color (the dominant non-background,
non-legend color). There are exactly as many shapes as markers.

The legend is a scaled-down map of where the shapes sit in the grid: each
marker's relative position inside the legend rectangle corresponds to one
shape's relative position in the grid. We match shapes to markers by
normalizing both sets of positions to the unit square and choosing the
assignment that minimizes total squared distance, then recolor each shape to
its matched marker's color. Everything else is left untouched.
"""

import itertools


def _components(grid, colorset):
    """4/8-connected components (8-connected) of cells whose color is in colorset."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colorset and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] not in colorset:
                        continue
                    seen.add((a, b))
                    comp.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(comp)
    return comps


def _normalize(pts):
    """Map (row, col) points into the unit square based on their bounding box."""
    ars = [p[0] for p in pts]
    acs = [p[1] for p in pts]
    mnr, mxr = min(ars), max(ars)
    mnc, mxc = min(acs), max(acs)
    out = []
    for p in pts:
        nr = (p[0] - mnr) / (mxr - mnr) if mxr > mnr else 0.0
        nc = (p[1] - mnc) / (mxc - mnc) if mxc > mnc else 0.0
        out.append((nr, nc))
    return out


def infer_T(input_grid):
    """Compute the recolor mask {(r, c): new_color} from the input alone."""
    H, W = len(input_grid), len(input_grid[0])

    # 1) Legend = largest connected block of color 5.
    fives = _components(input_grid, {5})
    if not fives:
        return {}
    legend = max(fives, key=len)
    rs = [r for r, c in legend]
    cs = [c for r, c in legend]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    # 2) Markers: non-5, non-background cells inside the legend bbox,
    #    recorded as (relative_row, relative_col, color).
    markers = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = input_grid[r][c]
            if v != 5 and v != 0:
                markers.append((r - r0, c - c0, v))
    if not markers:
        return {}

    # 3) Shapes: components of the dominant non-background, non-legend color.
    counts = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v != 5:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return {}
    base = max(counts, key=counts.get)
    shapes = _components(input_grid, {base})
    if not shapes:
        return {}

    # 4) Shape centroids.
    cents = []
    for sh in shapes:
        cr = sum(r for r, c in sh) / len(sh)
        cc = sum(c for r, c in sh) / len(sh)
        cents.append((cr, cc))

    # 5) Match shapes to markers via min total squared distance in unit-square
    #    normalized coordinates (the legend is a scaled map of the layout).
    nm = _normalize([(m[0], m[1]) for m in markers])
    ns = _normalize(cents)
    n = len(ns)
    best = None
    best_d = None
    for perm in itertools.permutations(range(len(nm)), n):
        d = sum((ns[i][0] - nm[perm[i]][0]) ** 2 +
                (ns[i][1] - nm[perm[i]][1]) ** 2 for i in range(n))
        if best_d is None or d < best_d:
            best_d = d
            best = perm

    # 6) Latent mask: recolor each shape's cells to its matched marker color.
    T = {}
    for i in range(n):
        new_color = markers[best[i]][2]
        for (r, c) in shapes[i]:
            T[(r, c)] = new_color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
