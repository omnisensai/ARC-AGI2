def infer_T(input_grid):
    """Infer a latent transformation mask (dict of (r,c)->color).

    Structure: a 'floor' row (a full row of a single non-bg color) sits at the
    bottom. Above it float several horizontal bars (one per occupied row, each a
    run of a single color). The transformation lets the bars fall and stack
    contiguously just above the floor, right-aligned, ordered longest-at-bottom
    to shortest-at-top.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Floor = bottom-most row that is entirely a single non-bg color.
    floor_row = None
    for r in range(H - 1, -1, -1):
        if len(set(input_grid[r])) == 1 and input_grid[r][0] != bg:
            floor_row = r
            break
    if floor_row is None:
        floor_row = H - 1

    # Collect bars from every other occupied row: (color, length).
    bars = []
    for r in range(H):
        if r == floor_row:
            continue
        nz = [v for v in input_grid[r] if v != bg]
        if not nz:
            continue
        bars.append((nz[0], len(nz)))

    # Longest first -> placed lowest (just above floor).
    bars.sort(key=lambda x: x[1], reverse=True)

    T = {}
    # Clear all non-bg cells above the floor.
    for r in range(floor_row):
        for c in range(W):
            if input_grid[r][c] != bg:
                T[(r, c)] = bg

    # Re-place bars stacked above the floor, right-aligned.
    row_idx = floor_row - 1
    for color, length in bars:
        if row_idx < 0:
            break
        for c in range(W - length, W):
            T[(row_idx, c)] = color
        row_idx -= 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
