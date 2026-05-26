def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # find connected components of non-background cells (8-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < H and 0 <= cc < W):
                    continue
                if seen[cr][cc] or g[cr][cc] == bg:
                    continue
                seen[cr][cc] = True
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((cr + dr, cc + dc))
            comps.append(cells)

    T = {}  # latent mask: (r,c) -> new color

    for cells in comps:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # border color = color on the outer frame corner of the bbox
        B = g[r0][c0]
        # interior fill color: the non-border, non-bg color inside the box
        Fcolor = None
        for (r, c) in cells:
            if g[r][c] != B:
                Fcolor = g[r][c]
        if Fcolor is None:
            continue
        ir = [r for (r, c) in cells if g[r][c] == Fcolor]
        ic = [c for (r, c) in cells if g[r][c] == Fcolor]
        ir0, ir1 = min(ir), max(ir)
        ic0, ic1 = min(ic), max(ic)
        s_h = ir1 - ir0 + 1  # interior height
        s_w = ic1 - ic0 + 1  # interior width

        # 1) inner square -> border color B (color swap)
        for r in range(ir0, ir1 + 1):
            for c in range(ic0, ic1 + 1):
                T[(r, c)] = B
        # 2) frame region (footprint minus inner) -> interior color F
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if ir0 <= r <= ir1 and ic0 <= c <= ic1:
                    continue
                T[(r, c)] = Fcolor
        # 3) cardinal arms of B extending outward by the interior dimension,
        #    spanning the full footprint width/height (diagonal corners stay bg)
        for r in range(r0 - s_h, r0):            # top arm
            for c in range(c0, c1 + 1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = B
        for r in range(r1 + 1, r1 + 1 + s_h):    # bottom arm
            for c in range(c0, c1 + 1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = B
        for c in range(c0 - s_w, c0):            # left arm
            for r in range(r0, r1 + 1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = B
        for c in range(c1 + 1, c1 + 1 + s_w):    # right arm
            for r in range(r0, r1 + 1):
                if 0 <= r < H and 0 <= c < W:
                    T[(r, c)] = B
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
