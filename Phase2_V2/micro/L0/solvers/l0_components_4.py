from collections import Counter, deque


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv and not seen[r][c]:
                color = g[r][c]; comp = set(); q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); comp.add((y, x))
                    for (ny, nx) in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == color:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(comp)
    comps.sort(key=lambda s: (min(r for r, _ in s), min(c for _, c in s)))
    T = {}
    for label, comp in enumerate(comps, start=1):
        for (r, c) in comp:
            T[(r, c)] = label
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
