def _components(grid):
    """8-connected components of color-8 cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 8 and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in seen or not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if grid[cr][cc] != 8:
                        continue
                    seen.add((cr, cc))
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(cells)
    return comps


def _canon_shape(cells):
    """Canonical key invariant to translation, rotation, reflection."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, c0 = min(rs), min(cs)
    base = [(r - r0, c - c0) for r, c in cells]
    variants = []
    cur = base
    for _ in range(4):
        cur = [(c, -r) for r, c in cur]  # rotate 90
        for v in (cur, [(r, -c) for r, c in cur]):  # plus reflection
            vr = [r for r, c in v]
            vc = [c for r, c in v]
            mr, mc = min(vr), min(vc)
            variants.append(frozenset((r - mr, c - mc) for r, c in v))
    return min(variants, key=lambda x: tuple(sorted(x)))


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}. Among the color-8 components, the two that
    are congruent (same shape under rotation/reflection) recolor to 1; the unique
    odd-shaped component recolors to 2."""
    comps = _components(input_grid)
    keys = [_canon_shape(c) for c in comps]
    T = {}
    for cells, key in zip(comps, keys):
        share = sum(1 for k in keys if k == key)
        color = 1 if share >= 2 else 2
        for (r, c) in cells:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
