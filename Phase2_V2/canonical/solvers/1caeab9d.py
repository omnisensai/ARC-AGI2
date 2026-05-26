def infer_T(input_grid):
    """Latent transformation: vertically shift every non-anchor object so its
    bounding-box top aligns with the row of the anchor object (color 1).
    Columns are preserved. Returns clear/paint masks."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Group non-background cells by color -> each color is one object.
    cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                cells.setdefault(v, []).append((r, c))

    if 1 not in cells:                      # no anchor -> identity
        return {}

    anchor_top = min(r for r, _ in cells[1])
    clears, paints = {}, {}
    for v, pts in cells.items():
        top = min(r for r, _ in pts)
        dr = anchor_top - top               # vertical shift to align tops
        if dr == 0:
            continue
        for (r, c) in pts:
            clears[(r, c)] = bg             # erase old position
        for (r, c) in pts:
            paints[(r + dr, c)] = v         # draw at shifted position
    return {"clears": clears, "paints": paints}


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    if not T:
        return out
    for (r, c), col in T["clears"].items():
        out[r][c] = col
    for (r, c), col in T["paints"].items():     # paints overwrite clears
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
