def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    # background = most common (0 gridlines or fill); foreground = the regular block color (1).
    # marker color = the color that is neither the most common nor the regular fill;
    # detect: colors present besides 0 and 1; pick the minority special color.
    bg = max(counts, key=counts.get)  # typically 0
    # The "normal" block color is the most common non-bg color.
    nonbg = {c: n for c, n in counts.items() if c != bg}
    normal = max(nonbg, key=nonbg.get) if nonbg else None
    specials = [c for c in nonbg if c != normal]
    if not specials:
        return [[None] * W for _ in range(H)]
    marker = min(specials, key=lambda c: counts[c])

    # marker cells
    mcells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == marker]
    mrows = set(r for r, c in mcells)
    mcols = set(c for r, c in mcells)

    # Determine row-band: maximal run of rows that are not entirely bg (gridline rows are all bg).
    def is_grid_row(r):
        return all(input_grid[r][c] == bg for c in range(W))

    def is_grid_col(c):
        return all(input_grid[r][c] == bg for r in range(H))

    # band id for each row
    row_band = [None] * H
    bid = 0
    in_band = False
    for r in range(H):
        if is_grid_row(r):
            in_band = False
        else:
            if not in_band:
                bid += 1
                in_band = True
            row_band[r] = bid
    col_band = [None] * W
    cid = 0
    in_band = False
    for c in range(W):
        if is_grid_col(c):
            in_band = False
        else:
            if not in_band:
                cid += 1
                in_band = True
            col_band[c] = cid

    marker_row_bands = set(row_band[r] for r in mrows if row_band[r] is not None)
    marker_col_bands = set(col_band[c] for c in mcols if col_band[c] is not None)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg:
                continue
            if row_band[r] in marker_row_bands or col_band[c] in marker_col_bands:
                T[r][c] = marker
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for r in range(len(out)):
        for c in range(len(out[0])):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
