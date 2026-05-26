def infer_T(input_grid):
    """Infer the latent mask: a copy of the multi-color shape stamped so that
    its bounding-box center lands on the lone `5` marker cell."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The lone marker cell (color 5) is the anchor center for the copy.
    marker = next(((r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] == 5), None)
    if marker is None:
        return {}

    # The shape: all non-background, non-marker cells (the multi-color object).
    shape = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] not in (bg, 5)]
    if not shape:
        return {}

    rs = [r for r, c in shape]
    cs = [c for r, c in shape]
    r0, c0 = min(rs), min(cs)
    bbox_h = max(rs) - r0 + 1
    bbox_w = max(cs) - c0 + 1
    cr, cc = bbox_h // 2, bbox_w // 2  # bbox center offset

    mr, mc = marker
    T = {}  # {(r, c): new_color} latent mask
    for (r, c) in shape:
        nr = mr - cr + (r - r0)
        nc = mc - cc + (c - c0)
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = input_grid[r][c]
    # The marker cell is replaced; if the stamp doesn't cover it, clear to bg.
    if marker not in T:
        T[marker] = bg
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
