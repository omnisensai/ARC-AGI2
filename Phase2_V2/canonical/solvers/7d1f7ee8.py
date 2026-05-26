"""Canonical solver for ARC puzzle 7d1f7ee8.

Rule: the grid contains several nested-rectangle "scenes". Each scene has an
outermost rectangle frame of some color, with other colored rectangles nested
inside it. Every shape that lives inside an outer frame is recolored to that
outermost frame's color; top-level (non-nested) shapes are left unchanged.

infer_T computes, for each connected colored component, whether it is nested
inside an outer component and what color its outermost container has, producing
a latent mask {(r,c): new_color}. apply_T overwrites only those masked cells.
"""


def _bg_of(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or g[y][x] != col:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((y + dy, x + dx))
                rs = [a for a, _ in cells]
                cs = [b for _, b in cells]
                comps.append({
                    'col': col,
                    'cells': cells,
                    'bb': (min(rs), min(cs), max(rs), max(cs)),
                })
    return comps


def _contains(a, b):
    """True if bounding box a strictly contains bounding box b."""
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return (ar0 <= br0 and ac0 <= bc0 and ar1 >= br1 and ac1 >= bc1
            and a != b)


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}: recolor nested shapes to their
    outermost container's frame color."""
    bg = _bg_of(input_grid)
    comps = _components(input_grid, bg)
    T = {}
    for ci, comp in enumerate(comps):
        containers = [cj for cj, o in enumerate(comps)
                      if cj != ci and _contains(o['bb'], comp['bb'])]
        if not containers:
            continue  # top-level shape: unchanged
        # outermost containers = those not contained by any other container
        tops = [cj for cj in containers
                if not any(ck != cj and _contains(comps[ck]['bb'], comps[cj]['bb'])
                           for ck in containers)]
        top = max(tops, key=lambda cj: (
            (comps[cj]['bb'][2] - comps[cj]['bb'][0]) *
            (comps[cj]['bb'][3] - comps[cj]['bb'][1])))
        target = comps[top]['col']
        for (y, x) in comp['cells']:
            T[(y, x)] = target
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
