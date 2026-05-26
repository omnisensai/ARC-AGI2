from collections import Counter


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            col = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if not (0 <= a < H and 0 <= b < W) or seen[a][b] or grid[a][b] != col:
                    continue
                seen[a][b] = True
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((a + dr, b + dc))
            rs = [x for x, _ in cells]
            cs = [y for _, y in cells]
            comps.append({
                'color': col, 'r0': min(rs), 'r1': max(rs),
                'c0': min(cs), 'c1': max(cs), 'n': len(cells),
            })
    return comps


def _legend(grid, bg):
    H, W = len(grid), len(grid[0])
    singles = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg:
                continue
            isolated = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dr, c + dc
                if 0 <= a < H and 0 <= b < W and grid[a][b] != bg:
                    isolated = False
                    break
            if isolated:
                singles.append((r, c, grid[r][c]))
    if not singles:
        return None, 0, 0
    r0 = min(r for r, _, _ in singles)
    c0 = min(c for _, c, _ in singles)
    nr = max((r - r0) // 2 for r, _, _ in singles) + 1
    nc = max((c - c0) // 2 for _, c, _ in singles) + 1
    L = [[None] * nc for _ in range(nr)]
    for r, c, v in singles:
        L[(r - r0) // 2][(c - c0) // 2] = v
    return L, r0, c0


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]

    L, _, _ = _legend(input_grid, bg)
    comps = _components(input_grid, bg)
    anchors = [cp for cp in comps if cp['n'] > 1]

    T = {}
    if L is None or not anchors:
        return T

    k = anchors[0]['r1'] - anchors[0]['r0'] + 1

    rstarts = sorted(set(a['r0'] for a in anchors))
    cstarts = sorted(set(a['c0'] for a in anchors))

    def stride(starts):
        diffs = [b - a for a, b in zip(starts, starts[1:])]
        return min(diffs) if diffs else None

    sr = stride(rstarts)
    sc = stride(cstarts)
    s = sr if sr is not None else sc
    if s is None:
        return T
    if sr is None:
        sr = s
    if sc is None:
        sc = s

    R0base = rstarts[0]
    C0base = cstarts[0]

    anchor_cells = []
    for a in anchors:
        bi = round((a['r0'] - R0base) / sr)
        bj = round((a['c0'] - C0base) / sc)
        anchor_cells.append((bi, bj, a['color']))

    nr = len(L)
    nc = len(L[0])

    best = None
    for oi in range(nr):
        for oj in range(nc):
            ok = True
            for bi, bj, col in anchor_cells:
                li, lj = oi + bi, oj + bj
                if not (0 <= li < nr and 0 <= lj < nc) or L[li][lj] != col:
                    ok = False
                    break
            if ok:
                best = (oi, oj)
                break
        if best:
            break
    if best is None:
        return T
    oi, oj = best

    R_origin = R0base - oi * sr
    C_origin = C0base - oj * sc

    for i in range(nr):
        for j in range(nc):
            color = L[i][j]
            if color is None:
                continue
            br = R_origin + i * sr
            bc = C_origin + j * sc
            for dr in range(k):
                for dc in range(k):
                    r, c = br + dr, bc + dc
                    if 0 <= r < H and 0 <= c < W:
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
