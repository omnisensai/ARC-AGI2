from collections import Counter, deque


def _components_by_colour(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True; q.append((ny, nx))
            comps.append((col, cells))
    return comps


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    if len(comps) != 2:
        return {}
    solid = hollow = None
    for col, cells in comps:
        rmin = min(r for r, _ in cells); rmax = max(r for r, _ in cells)
        cmin = min(c for _, c in cells); cmax = max(c for _, c in cells)
        bbox_size = (rmax - rmin + 1) * (cmax - cmin + 1)
        if len(cells) == bbox_size:
            solid = (col, cells, (rmin, rmax, cmin, cmax))
        else:
            # hollow: cells lie on the bbox boundary only
            boundary = {(r, c) for r in (rmin, rmax) for c in range(cmin, cmax + 1)}                      | {(r, c) for c in (cmin, cmax) for r in range(rmin, rmax + 1)}
            if set(cells) == boundary:
                hollow = (col, cells, (rmin, rmax, cmin, cmax))
    if solid is None or hollow is None:
        return {}

    _, solid_cells, (sr0, sr1, sc0, sc1) = solid
    sol_h = sr1 - sr0 + 1; sol_w = sc1 - sc0 + 1
    solid_col = solid[0]
    _, _, (hr0, hr1, hc0, hc1) = hollow
    hollow_inner_h = hr1 - hr0 - 1; hollow_inner_w = hc1 - hc0 - 1
    if (sol_h, sol_w) != (hollow_inner_h, hollow_inner_w):
        return {}

    T = {}
    for (y, x) in solid_cells:
        T[(y, x)] = bg
    for r in range(hr0 + 1, hr1):
        for c in range(hc0 + 1, hc1):
            T[(r, c)] = solid_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
