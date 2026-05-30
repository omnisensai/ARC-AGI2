from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    # marker = rarest non-bg colour; outline = the other non-bg colour
    if len(counts) < 2:
        return {}
    marker_col = min(counts, key=lambda k: counts[k])
    outline_col = next(c for c in counts if c != marker_col)

    # Border flood -> "outside"
    outside = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and g[r][c] == bg and (r, c) not in outside:
                outside.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in outside:
                outside.add((nr, nc)); q.append((nr, nc))
    interior = [(r, c) for r in range(H) for c in range(W)
                if g[r][c] == bg and (r, c) not in outside]
    if not interior:
        return {}
    # Anchor parity: top-left interior cell becomes outline_col.
    r0 = min(r for r, c in interior); c0 = min(c for r, c in interior if r == r0)
    anchor_parity = (r0 + c0) % 2
    T = {}
    for (r, c) in interior:
        T[(r, c)] = outline_col if (r + c) % 2 == anchor_parity else marker_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
