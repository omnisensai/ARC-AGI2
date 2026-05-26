def infer_T(input_grid):
    """Infer the latent transformation mask.

    Each connected component is a closed rectangular outline of the foreground
    color (6) on the background (8). The transformation:
      - fills enclosed background holes inside the outline with color 4
      - draws a color-3 ring one cell outside the component's bounding box
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    fg = None
    for v in counts:
        if v != bg:
            fg = v
            break

    # connected components of fg cells (8-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == fg and not seen[r][c]:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[cr][cc] or input_grid[cr][cc] != fg:
                        continue
                    seen[cr][cc] = True
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((cr + dr, cc + dc))
                comps.append(comp)

    T = {}
    for comp in comps:
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # background cells within the bounding box
        inside = set()
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                if input_grid[rr][cc] == bg:
                    inside.add((rr, cc))
        # flood-fill from bbox-border bg cells; whatever is unreachable is enclosed
        reachable = set()
        stack = [(rr, cc) for (rr, cc) in inside
                 if rr == r0 or rr == r1 or cc == c0 or cc == c1]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in reachable or (cr, cc) not in inside:
                continue
            reachable.add((cr, cc))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((cr + dr, cc + dc))
        for (rr, cc) in inside - reachable:
            T[(rr, cc)] = 4

        # color-3 ring one cell outside the bounding box
        for cc in range(c0 - 1, c1 + 2):
            for rr in (r0 - 1, r1 + 1):
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = 3
        for rr in range(r0 - 1, r1 + 2):
            for cc in (c0 - 1, c1 + 1):
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
