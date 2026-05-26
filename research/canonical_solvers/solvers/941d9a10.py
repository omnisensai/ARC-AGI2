def _regions(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    regs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or g[y][x] != bg:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
                regs.append(cells)
    return regs


def infer_T(input_grid):
    # The grid is partitioned into rectangular cells by gridlines of the
    # most-common (line) color. Background cells are connected regions of 0.
    # Mark three special regions:
    #   1 -> region touching top-left corner (0,0)
    #   3 -> region touching bottom-right corner (H-1,W-1)
    #   2 -> region whose bounding-box center is nearest the grid center
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    # background = the cell color (0 here), line color = the separator.
    # Use the value at the corner if it is not the line color; otherwise pick
    # the most common non-line color. Lines are the most frequent color.
    line = max(counts, key=counts.get)
    bg_candidates = [v for v in counts if v != line]
    bg = max(bg_candidates, key=counts.get) if bg_candidates else line

    regs = _regions(input_grid, bg)
    T = [[None] * W for _ in range(H)]
    if not regs:
        return T

    gc = ((H - 1) / 2.0, (W - 1) / 2.0)
    region_tl = None
    region_br = None
    region_center = None
    best_dist = None
    for cells in regs:
        cellset = set(cells)
        if (0, 0) in cellset:
            region_tl = cells
        if (H - 1, W - 1) in cellset:
            region_br = cells
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        cy = (min(rs) + max(rs)) / 2.0
        cx = (min(cs) + max(cs)) / 2.0
        dist = (cy - gc[0]) ** 2 + (cx - gc[1]) ** 2
        if best_dist is None or dist < best_dist:
            best_dist = dist
            region_center = cells

    if region_center is not None:
        for y, x in region_center:
            T[y][x] = 2
    if region_tl is not None:
        for y, x in region_tl:
            T[y][x] = 1
    if region_br is not None:
        for y, x in region_br:
            T[y][x] = 3
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
