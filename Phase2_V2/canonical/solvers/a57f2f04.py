def regions_of(g):
    """Connected components of non-background (non-8) cells -> bounding boxes."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 8 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or a >= H or b < 0 or b >= W or seen[a][b] or g[a][b] == 8:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((a + dr, b + dc))
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                res.append((min(rs), max(rs), min(cs), max(cs)))
    return res


def infer_T(input_grid):
    """For each 0-filled rectangular region containing a small colored stamp in
    one corner, tile that stamp (its colored-cell bounding box) periodically
    across the whole region, anchored to the stamp's corner."""
    g = input_grid
    T = {}
    for (r0, r1, c0, c1) in regions_of(g):
        Hr, Wr = r1 - r0 + 1, c1 - c0 + 1
        colored = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                   if g[r][c] not in (0, 8)]
        if not colored:
            continue
        rr = [r for r, _ in colored]
        cc = [c for _, c in colored]
        sr0, sr1 = min(rr), max(rr)
        sc0, sc1 = min(cc), max(cc)
        kh, kw = sr1 - sr0 + 1, sc1 - sc0 + 1
        tile = [[g[sr0 + i][sc0 + j] for j in range(kw)] for i in range(kh)]
        top = (sr0 - r0) == 0   # stamp flush to top edge of region?
        left = (sc0 - c0) == 0  # stamp flush to left edge of region?
        for i in range(Hr):
            ti = i % kh if top else (i - (Hr - kh)) % kh
            for j in range(Wr):
                tj = j % kw if left else (j - (Wr - kw)) % kw
                T[(r0 + i, c0 + j)] = tile[ti][tj]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
