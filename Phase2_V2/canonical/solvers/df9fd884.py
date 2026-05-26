"""Canonical latent-T solver for ARC puzzle df9fd884.

Structure: the grid contains two 3-sided "bracket" boxes drawn in one color
(here 4), each with an opening on one side, plus a small colored payload object
that sits next to one of the boxes. The payload is transferred to the OTHER box:
it is placed at that box's mouth (aligned to the opening columns/rows) and slid
through the opening all the way to the grid edge in the opening direction. The
payload keeps its shape; its original cells revert to background.

infer_T builds a latent mask {(r,c): new_color} of the cells to overwrite (the
new payload location plus the vacated original cells); apply_T copies the input
and overwrites only those cells.
"""


def _components(grid, color, H, W):
    seen = set(); out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]; comp = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b)); comp.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                out.append(comp)
    return out


def _bg_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _container_info(comp, H, W):
    s = set(comp)
    rs = [r for r, c in comp]; cs = [c for r, c in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    top = all((r0, c) in s for c in range(c0, c1 + 1))
    bot = all((r1, c) in s for c in range(c0, c1 + 1))
    left = all((r, c0) in s for r in range(r0, r1 + 1))
    right = all((r, c1) in s for r in range(r0, r1 + 1))
    opening = None
    if not bot:
        opening = 'down'
    elif not top:
        opening = 'up'
    elif not right:
        opening = 'right'
    elif not left:
        opening = 'left'
    gaps = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if (r, c) not in s]
    return {'r0': r0, 'r1': r1, 'c0': c0, 'c1': c1, 'opening': opening,
            'gapcols': sorted(set(c for r, c in gaps)),
            'gaprows': sorted(set(r for r, c in gaps))}


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg_color(input_grid)

    counts = {}
    for row in input_grid:
        for v in row:
            if v != bg:
                counts[v] = counts.get(v, 0) + 1

    # container color forms exactly two multi-cell bracket components.
    cont_color = None
    for color in counts:
        comps = _components(input_grid, color, H, W)
        if len(comps) == 2 and all(len(c) >= 3 for c in comps):
            cont_color = color

    # payload = remaining non-background, non-container color.
    payload_color = None
    payload_cells = None
    for color in counts:
        if color == cont_color:
            continue
        cells = [(r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == color]
        if cells:
            payload_color = color
            payload_cells = cells

    T = {}
    if cont_color is None or payload_cells is None:
        return T

    comps = _components(input_grid, cont_color, H, W)
    containers = [_container_info(comp, H, W) for comp in comps]

    pr0 = min(r for r, c in payload_cells); pr1 = max(r for r, c in payload_cells)
    pc0 = min(c for r, c in payload_cells); pc1 = max(c for r, c in payload_cells)
    pcr = (pr0 + pr1) / 2.0; pcc = (pc0 + pc1) / 2.0

    def dist(ci):
        cr = (ci['r0'] + ci['r1']) / 2.0; cc = (ci['c0'] + ci['c1']) / 2.0
        return abs(cr - pcr) + abs(cc - pcc)

    # the payload is transferred to the FAR container (not the one it sits by).
    target = max(containers, key=dist)

    offs = sorted((r - pr0, c - pc0) for r, c in payload_cells)
    ph = pr1 - pr0 + 1
    pw = pc1 - pc0 + 1

    opening = target['opening']
    if opening in ('down', 'up'):
        base_c = target['gapcols'][0]
        base_r = H - ph if opening == 'down' else 0
    else:
        base_r = target['gaprows'][0]
        base_c = W - pw if opening == 'right' else 0

    # place payload at its new location
    for dr, dc in offs:
        T[(base_r + dr, base_c + dc)] = payload_color
    # vacate original payload cells (revert to background) where not reused
    for (r, c) in payload_cells:
        if (r, c) not in T:
            T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
