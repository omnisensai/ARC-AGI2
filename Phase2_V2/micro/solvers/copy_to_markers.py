from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    proto = max(comps, key=len)                       # prototype = largest component
    C = g[proto[0][0]][proto[0][1]]
    pr0 = min(r for r, c in proto); pc0 = min(c for r, c in proto)
    offs = [(r - pr0, c - pc0) for (r, c) in proto]
    markers = [cells[0] for cells in comps if len(cells) == 1 and g[cells[0][0]][cells[0][1]] != C]
    T = {}
    for (mr, mc) in markers:
        for (dr, dc) in offs:
            nr, nc = mr + dr, mc + dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = C
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
