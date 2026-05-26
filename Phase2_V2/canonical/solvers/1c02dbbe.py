from collections import defaultdict


def infer_T(input_grid):
    """Latent mask: each marker-color spans a rectangle from its corner anchor
    on the 5-block to the row/col lines given by its two edge markers."""
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1

    # background = most common color on the outer border of the grid
    border = []
    for c in range(W):
        border.append(input_grid[0][c])
        border.append(input_grid[H - 1][c])
    for r in range(H):
        border.append(input_grid[r][0])
        border.append(input_grid[r][W - 1])
    bcount = {}
    for v in border:
        bcount[v] = bcount.get(v, 0) + 1
    bg = max(bcount, key=bcount.get)

    # rectangle fill color = most common non-bg color (the big solid block)
    nonbg = {c: n for c, n in counts.items() if c != bg}
    rect_color = max(nonbg, key=nonbg.get) if nonbg else None

    rect_cells = [(r, c) for r in range(H) for c in range(W)
                  if input_grid[r][c] == rect_color]
    rs = [r for r, c in rect_cells]
    cs = [c for r, c in rect_cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    # collect markers: every color that is neither bg nor the rect fill
    markers = defaultdict(list)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != rect_color:
                markers[v].append((r, c))

    T = [[None] * W for _ in range(H)]
    for color, pts in markers.items():
        corner = None
        line_row = None  # row index from a left/right edge marker
        line_col = None  # col index from a top/bottom edge marker
        for (r, c) in pts:
            T[r][c] = bg  # markers are erased to background
            if r0 <= r <= r1 and c0 <= c <= c1:
                corner = (r, c)
            elif r < r0 or r > r1:
                line_col = c  # marker above/below the block -> defines column extent
            elif c < c0 or c > c1:
                line_row = r  # marker left/right of the block -> defines row extent
        if corner is None or line_row is None or line_col is None:
            continue
        cr, cc = corner
        rr0, rr1 = sorted((cr, line_row))
        cc0, cc1 = sorted((cc, line_col))
        for r in range(rr0, rr1 + 1):
            for c in range(cc0, cc1 + 1):
                T[r][c] = color
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
