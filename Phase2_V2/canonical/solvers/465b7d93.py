def infer_T(input_grid):
    """Latent mask: project a small corner-marker shape onto the box interior.

    Structure of every pair:
      - A hollow rectangle drawn in color 6 (a container box).
      - A separate small shape (some other non-background color) whose marked
        cells sit at corners of its own bounding box.
    The shape's marked corners select which edges of the box INTERIOR get drawn
    as full lines (an edge is drawn iff both its endpoint corners are marked).
    Any interior region fully enclosed by the drawn edges is then filled, and
    the original shape is erased to background.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    box = 6

    T = {}
    cells6 = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == box]
    if not cells6:
        return T
    r0 = min(r for r, c in cells6); r1 = max(r for r, c in cells6)
    c0 = min(c for r, c in cells6); c1 = max(c for r, c in cells6)
    ir0, ir1, ic0, ic1 = r0 + 1, r1 - 1, c0 + 1, c1 - 1
    ih = ir1 - ir0 + 1
    iw = ic1 - ic0 + 1
    if ih <= 0 or iw <= 0:
        return T

    shape = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg and input_grid[r][c] != box]
    if not shape:
        return T
    color = input_grid[shape[0][0]][shape[0][1]]
    sr0 = min(r for r, c in shape); sr1 = max(r for r, c in shape)
    sc0 = min(c for r, c in shape); sc1 = max(c for r, c in shape)
    sh = sr1 - sr0 + 1
    sw = sc1 - sc0 + 1
    sset = set(shape)

    def marked(i, j):
        return (sr0 + i, sc0 + j) in sset

    TL = marked(0, 0)
    TR = marked(0, sw - 1)
    BL = marked(sh - 1, 0)
    BR = marked(sh - 1, sw - 1)

    # Draw full interior edge lines for adjacent marked-corner pairs.
    fill = [[False] * iw for _ in range(ih)]
    if TL and TR:
        for j in range(iw): fill[0][j] = True
    if BL and BR:
        for j in range(iw): fill[ih - 1][j] = True
    if TL and BL:
        for i in range(ih): fill[i][0] = True
    if TR and BR:
        for i in range(ih): fill[i][iw - 1] = True

    # Flood-fill from the interior border across undrawn cells; whatever is NOT
    # reachable is enclosed by the drawn edges and must be filled too.
    reach = [[False] * iw for _ in range(ih)]
    stack = []
    for i in range(ih):
        for j in range(iw):
            if (i == 0 or j == 0 or i == ih - 1 or j == iw - 1) and not fill[i][j]:
                stack.append((i, j))
    while stack:
        i, j = stack.pop()
        if i < 0 or j < 0 or i >= ih or j >= iw:
            continue
        if reach[i][j] or fill[i][j]:
            continue
        reach[i][j] = True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((i + di, j + dj))

    for i in range(ih):
        for j in range(iw):
            if fill[i][j] or not reach[i][j]:
                T[(ir0 + i, ic0 + j)] = color

    # Erase the original shape.
    for (r, c) in shape:
        T[(r, c)] = bg

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
