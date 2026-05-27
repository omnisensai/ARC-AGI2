from collections import Counter, deque

NB8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if not nz:
        return {}
    C = max(nz, key=lambda k: nz[k])              # neutral object colour = most common non-bg
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == C and not seen[r][c]:
                comp = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == C:
                            seen[ny][nx] = True; q.append((ny, nx))
                mark = None
                for (y, x) in comp:
                    for dy, dx in NB8:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != bg and g[ny][nx] != C:
                            mark = g[ny][nx]; break
                    if mark is not None:
                        break
                if mark is not None:
                    for (y, x) in comp:
                        T[(y, x)] = mark
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
