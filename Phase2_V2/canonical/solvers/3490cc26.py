def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _blocks(g):
    """Return list of (top_row, left_col, color) for each connected colored block."""
    H, W = len(g), len(g[0])
    seen = set()
    res = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and (r, c) not in seen:
                col = g[r][c]
                stack = [(r, c)]
                seen.add((r, c))
                comp = [(r, c)]
                while stack:
                    a, b = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            na, nb = a + dr, b + dc
                            if 0 <= na < H and 0 <= nb < W and g[na][nb] == col and (na, nb) not in seen:
                                seen.add((na, nb))
                                stack.append((na, nb))
                                comp.append((na, nb))
                rs = [x[0] for x in comp]
                cs = [x[1] for x in comp]
                res.append((min(rs), min(cs), col))
    return res


def infer_T(input_grid):
    """Latent mask: trace a greedy snake of 7-bridges through the blocks.

    All non-background cells form 2x2 blocks. Exactly one block is color 2 (the
    seed); the rest are color 8. Starting from the seed, repeatedly hop to the
    nearest still-unvisited block that is row-aligned or column-aligned with the
    current block (the nearest block along each of the four axis directions is a
    candidate; the globally closest of those is chosen). Each hop fills the empty
    gap between the two blocks with color 7, producing a single non-revisiting
    path. Blocks unreachable from this snake are left untouched.
    """
    H, W = len(input_grid), len(input_grid[0])
    blocks = _blocks(input_grid)
    pos = [(r, c) for r, c, col in blocks]

    start = None
    for r, c, col in blocks:
        if col == 2:
            start = (r, c)
            break

    T = [[None] * W for _ in range(H)]
    if start is None or len(blocks) < 2:
        return T

    def nearest_in_dir(cur, dirn):
        r0, c0 = cur
        if dirn == 'R':
            cand = [cc for (rr, cc) in pos if rr == r0 and cc > c0]
            return (r0, min(cand)) if cand else None
        if dirn == 'L':
            cand = [cc for (rr, cc) in pos if rr == r0 and cc < c0]
            return (r0, max(cand)) if cand else None
        if dirn == 'D':
            cand = [rr for (rr, cc) in pos if cc == c0 and rr > r0]
            return (min(cand), c0) if cand else None
        cand = [rr for (rr, cc) in pos if cc == c0 and rr < r0]
        return (max(cand), c0) if cand else None

    visited = {start}
    cur = start
    edges = []
    while True:
        best = None
        bestd = None
        for dirn in ('R', 'L', 'D', 'U'):
            tgt = nearest_in_dir(cur, dirn)
            if tgt is not None and tgt not in visited:
                dist = abs(tgt[0] - cur[0]) + abs(tgt[1] - cur[1])
                if bestd is None or dist < bestd:
                    bestd = dist
                    best = tgt
        if best is None:
            break
        edges.append((cur, best))
        visited.add(best)
        cur = best

    for a, b in edges:
        if a[0] == b[0]:  # horizontal bridge (blocks are 2 rows tall)
            r = a[0]
            c1, c2 = sorted((a[1], b[1]))
            for cc in range(c1 + 2, c2):
                T[r][cc] = 7
                T[r + 1][cc] = 7
        else:  # vertical bridge (blocks are 2 cols wide)
            c = a[1]
            r1, r2 = sorted((a[0], b[0]))
            for rr in range(r1 + 2, r2):
                T[rr][c] = 7
                T[rr][c + 1] = 7
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
