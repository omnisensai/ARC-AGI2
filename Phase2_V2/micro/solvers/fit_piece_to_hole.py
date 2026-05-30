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
    # Find a pair of components with matching normalized shape.
    pairs = []
    for i in range(3):
        for j in range(i + 1, 3):
            if _normalize(comps[i][1]) == _normalize(comps[j][1]):
                pairs.append((i, j))
    if len(pairs) != 1:
        return {}
    i, j = pairs[0]
    # The third component is the non-matching piece (irrelevant); pick one of
    # the matching pair as ghost (destination) and the other as source. We use
    # the deterministic rule: source = the one whose top-left (row, col) is
    # smaller. This makes the rule reversible from the data without an
    # explicit marker.
    a_cells = comps[i][1]; b_cells = comps[j][1]
    a_tl = (min(r for r, _ in a_cells), min(c for _, c in a_cells))
    b_tl = (min(r for r, _ in b_cells), min(c for _, c in b_cells))
    if a_tl < b_tl:
        src = comps[i]; dst = comps[j]
    else:
        src = comps[j]; dst = comps[i]
    src_col, src_cells = src
    dst_col, dst_cells = dst

    T = {}
    for (y, x) in src_cells:
        T[(y, x)] = bg
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
