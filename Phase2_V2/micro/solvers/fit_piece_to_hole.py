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
    pieces = []; outline = None
    for col, cells in comps:
        rmin = min(r for r, _ in cells); rmax = max(r for r, _ in cells)
        cmin = min(c for _, c in cells); cmax = max(c for _, c in cells)
        bbox_size = (rmax - rmin + 1) * (cmax - cmin + 1)
        if len(cells) == bbox_size:
            pieces.append((col, cells, (rmin, rmax, cmin, cmax)))
        else:
            boundary = {(r, c) for r in (rmin, rmax) for c in range(cmin, cmax + 1)}                      | {(r, c) for c in (cmin, cmax) for r in range(rmin, rmax + 1)}
            if set(cells) == boundary:
                outline = (col, cells, (rmin, rmax, cmin, cmax))
    if outline is None or len(pieces) < 1:
        return {}

    _, _, (hr0, hr1, hc0, hc1) = outline
    inner_h = hr1 - hr0 - 1; inner_w = hc1 - hc0 - 1

    matching = None
    for p in pieces:
        _, _, (pr0, pr1, pc0, pc1) = p
        if (pr1 - pr0 + 1, pc1 - pc0 + 1) == (inner_h, inner_w):
            matching = p; break
    if matching is None:
        return {}
    match_col, match_cells, _ = matching

    T = {}
    for (y, x) in match_cells:
        T[(y, x)] = bg
    for r in range(hr0 + 1, hr1):
        for c in range(hc0 + 1, hc1):
            T[(r, c)] = match_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
