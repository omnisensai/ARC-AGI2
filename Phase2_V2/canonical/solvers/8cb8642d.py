def _components(grid):
    """Connected components (4-conn) of all non-background (non-zero) cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if not seen[r][c] and grid[r][c] != 0:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or grid[y][x] == 0:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _marked(i, j, IH, IW):
    """True if interior cell (i,j) lies on the inward diagonal/spine pattern."""
    dr = min(i, IH - 1 - i)          # depth from top/bottom edge
    dc = min(j, IW - 1 - j)          # depth from left/right edge
    if dr == dc:                     # on a corner diagonal ray
        return True
    m = min((IH - 1) // 2, (IW - 1) // 2)   # depth at which the shorter dim centers
    if IH > IW and dc == m and dr >= m:      # vertical spine (taller box)
        return True
    if IW > IH and dr == m and dc >= m:      # horizontal spine (wider box)
        return True
    return False


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}. For each filled rectangle (a solid color
    region carrying one differently-colored marker cell): clear its interior to 0
    and draw diagonal rays from the four interior corners in the marker color,
    the rays bouncing along the center spine of the longer dimension."""
    T = {}
    for cells in _components(input_grid):
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        # only treat solid bounding-box rectangles (full block) as targets
        if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
            continue
        counts = {}
        for y, x in cells:
            counts[input_grid[y][x]] = counts.get(input_grid[y][x], 0) + 1
        fill = max(counts, key=counts.get)
        marker_colors = [input_grid[y][x] for y, x in cells if input_grid[y][x] != fill]
        if not marker_colors:
            continue
        mc = marker_colors[0]
        IH, IW = r1 - r0 - 1, c1 - c0 - 1
        if IH <= 0 or IW <= 0:
            continue
        for i in range(IH):
            for j in range(IW):
                rr, cc = r0 + 1 + i, c0 + 1 + j
                T[(rr, cc)] = mc if _marked(i, j, IH, IW) else 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
