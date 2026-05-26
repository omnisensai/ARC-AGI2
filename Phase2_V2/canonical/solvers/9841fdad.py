def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # border/separator color = the outer-frame color (corner of grid)
    border = input_grid[0][0]

    # full columns of border color split the grid into panels
    is_full = [all(input_grid[r][c] == border for r in range(H)) for c in range(W)]
    segments = []
    c = 0
    while c < W:
        if not is_full[c]:
            start = c
            while c < W and not is_full[c]:
                c += 1
            segments.append((start, c - 1))
        else:
            c += 1

    # interior rows (skip full border rows)
    is_full_row = [all(input_grid[r][c] == border for c in range(W)) for r in range(H)]
    rows = [r for r in range(H) if not is_full_row[r]]
    r0, r1 = rows[0], rows[-1]

    panels = list(segments)

    def panel_colors(c0, c1):
        s = set()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                s.add(input_grid[r][c])
        return s

    # key panel = the one with the most distinct colors (frame + shapes);
    # canvas panel = the uniformly filled one.
    keyidx = max(range(len(panels)), key=lambda i: len(panel_colors(*panels[i])))
    canvidx = [i for i in range(len(panels)) if i != keyidx][0]
    kc0, kc1 = panels[keyidx]
    vc0, vc1 = panels[canvidx]

    frame = input_grid[r0][kc0]      # key panel's frame color
    # interiors (inside frames)
    ki0, ki1 = kc0 + 1, kc1 - 1
    kr0, kr1 = r0 + 1, r1 - 1
    kwidth = ki1 - ki0 + 1
    vi0, vi1 = vc0 + 1, vc1 - 1
    vwidth = vi1 - vi0 + 1

    # connected components of non-frame cells inside key interior (4-connected, same color)
    seen = set()
    comps = []
    for r in range(kr0, kr1 + 1):
        for c in range(ki0, ki1 + 1):
            if (r, c) in seen:
                continue
            v = input_grid[r][c]
            if v == frame:
                continue
            stack = [(r, c)]
            comp = []
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (kr0 <= nr <= kr1 and ki0 <= nc <= ki1
                            and (nr, nc) not in seen and input_grid[nr][nc] == v):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((v, comp))

    # Map each key shape onto the canvas: rows align directly. Horizontally, a shape
    # anchored to the left interior wall is placed at the canvas' left wall (same width);
    # anchored to the right wall -> canvas right wall; spanning the full key width ->
    # stretched across the full canvas width. (Free-floating shapes: proportional.)
    T = {}
    for v, comp in comps:
        rmin = min(p[0] for p in comp); rmax = max(p[0] for p in comp)
        cmin = min(p[1] for p in comp); cmax = max(p[1] for p in comp)
        touch_left = cmin == ki0
        touch_right = cmax == ki1
        w = cmax - cmin + 1
        if touch_left and touch_right:
            ncmin, ncmax = vi0, vi1
        elif touch_left:
            ncmin, ncmax = vi0, vi0 + w - 1
        elif touch_right:
            ncmin, ncmax = vi1 - w + 1, vi1
        else:
            off = round((cmin - ki0) * vwidth / kwidth)
            ncmin = vi0 + off
            ncmax = ncmin + w - 1
        for r in range(rmin, rmax + 1):
            for c in range(ncmin, ncmax + 1):
                T[(r, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
