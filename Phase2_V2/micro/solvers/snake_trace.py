from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    if len(counts) < 2:
        return {}
    # Snake = the rarest non-bg colour (single seed cell).
    snake_col = min(counts, key=lambda k: counts[k])
    wall_col = next(c for c in counts if c != snake_col)

    wall = {(r, c) for r in range(H) for c in range(W) if g[r][c] == wall_col}
    if not wall:
        return {}

    # Exterior = cells reachable from grid border via 4-conn flood, treating
    # wall cells as blockers. (Snake seed cell is non-bg too -> treat as
    # non-blocker by skipping the wall check when expanding into it; but its
    # cell isn't bg so we exclude it from exterior set computation.)
    exterior = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and (r, c) not in wall:
                if (r, c) not in exterior:
                    exterior.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in wall and (nr, nc) not in exterior:
                exterior.add((nr, nc)); q.append((nr, nc))

    T = {}
    for (r, c) in exterior:
        # already-coloured cells (the snake seed) stay; we still write T but
        # the value equals their existing colour.
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in wall:
                if g[r][c] == bg:
                    T[(r, c)] = snake_col
                break
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
