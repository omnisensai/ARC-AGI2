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


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    if len(comps) != 3:
        return {}
    # Marker = the singleton component (1 cell)
    marker = next((c for c in comps if len(c[1]) == 1), None)
    blobs  = [c for c in comps if len(c[1]) > 1]
    if marker is None or len(blobs) != 2:
        return {}
    # Both blobs must be the same shape
    if _normalize(blobs[0][1]) != _normalize(blobs[1][1]):
        return {}
    marker_col, marker_cells = marker
    mr, mc = marker_cells[0]
    # Source = blob with a cell 4-adjacent to the marker.
    src = None; dst = None
    for blob in blobs:
        cells = set(blob[1])
        for (y, x) in cells:
            if abs(y - mr) + abs(x - mc) == 1:
                src = blob; break
        if src is blob:
            continue
    src = src or blobs[0]
    dst = blobs[1] if src is blobs[0] else blobs[0]
    src_col, src_cells = src
    dst_col, dst_cells = dst

    T = {}
    for (y, x) in src_cells:
        T[(y, x)] = bg
    T[(mr, mc)] = bg
    for (y, x) in dst_cells:
        T[(y, x)] = src_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
