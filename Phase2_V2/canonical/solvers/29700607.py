def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Find the key: a horizontal run of non-bg cells in a single row.
    # Identify all non-bg cells.
    nonbg = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W)
             if input_grid[r][c] != bg]

    # The key is the row that contains >=2 horizontally-adjacent non-bg cells
    # forming a contiguous horizontal run. Group by row.
    rows_cells = {}
    for r, c, v in nonbg:
        rows_cells.setdefault(r, []).append((c, v))

    key_row = None
    key_cells = None
    for r, cells in rows_cells.items():
        cells_sorted = sorted(cells)
        cols = [c for c, v in cells_sorted]
        if len(cols) >= 2 and cols == list(range(min(cols), max(cols) + 1)):
            key_row = r
            key_cells = cells_sorted  # list of (col, color)
            break

    # Map each key color -> its column
    color_to_keycol = {v: c for c, v in key_cells}

    # Markers are non-bg cells not in the key row
    markers = [(r, c, v) for r, c, v in nonbg if r != key_row]

    T = {}
    for c, v in key_cells:
        T[(key_row, c)] = v

    marker_colors = {mv for _, _, mv in markers}

    # Key colors without a marker: vertical line extends to the bottom edge.
    for c, v in key_cells:
        if v not in marker_colors:
            for rr in range(key_row, H):
                T[(rr, c)] = v

    for mr, mc, mv in markers:
        if mv not in color_to_keycol:
            continue
        kc = color_to_keycol[mv]
        # Vertical line at key column from key_row down to marker row
        lo, hi = min(key_row, mr), max(key_row, mr)
        for rr in range(lo, hi + 1):
            T[(rr, kc)] = mv
        # Horizontal line at marker row from marker column toward key column
        c0, c1 = min(mc, kc), max(mc, kc)
        for cc in range(c0, c1 + 1):
            T[(mr, cc)] = mv

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
