from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
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
    if len(comps) != 2:
        return {}
    col = comps[0][0]
    blob_cells = set(comps[0][1]) | set(comps[1][1])
    centroids = []
    for _, cells in comps:
        cr = sum(r for r, c in cells) // len(cells)
        cc = sum(c for r, c in cells) // len(cells)
        centroids.append((cr, cc))
    (r1, c1), (r2, c2) = centroids
    T = {}
    if r1 == r2:
        step = 1 if c2 > c1 else -1
        for c in range(c1 + step, c2, step):
            if (r1, c) not in blob_cells:
                T[(r1, c)] = col
    elif c1 == c2:
        step = 1 if r2 > r1 else -1
        for r in range(r1 + step, r2, step):
            if (r, c1) not in blob_cells:
                T[(r, c1)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
