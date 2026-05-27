from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if len(nz) < 2:
        return {}
    M = min(nz, key=lambda k: nz[k])          # seed/marker = rarest non-bg colour
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and g[r][c] != M and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    if not comps:
        return {}
    largest = max(comps, key=len)
    T = {}
    for cells in comps:
        tgt = M if cells is largest else bg
        for (y, x) in cells:
            T[(y, x)] = tgt
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
