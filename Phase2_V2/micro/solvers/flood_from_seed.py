from collections import Counter, deque

NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    S = min(nz, key=lambda k: nz[k])              # seed = rarest non-bg (single cell)
    sr, sc = next((r, c) for r in range(H) for c in range(W) if g[r][c] == S)
    seen = set(); q = deque()
    for dr, dc in NB:
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg:
            seen.add((nr, nc)); q.append((nr, nc))
    while q:
        r, c = q.popleft()
        for dr, dc in NB:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append((nr, nc))
    return {(r, c): S for (r, c) in seen}


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
