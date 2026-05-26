"""Canonical solver for ARC puzzle c444b776.

Structure: the grid is divided into rectangular panels by full lines (rows
and/or columns) of a single separator color. Exactly one panel contains a
non-empty pattern (the template); the remaining panels are empty (background).
The transformation copies the template pattern into every empty panel.

Latent T: a dict {(r,c): color} of cells that must be overwritten so that every
panel matches the template's relative content.
"""


def _counts(grid):
    c = {}
    for row in grid:
        for v in row:
            c[v] = c.get(v, 0) + 1
    return c


def _background(grid):
    return max(_counts(grid).items(), key=lambda kv: kv[1])[0]


def _separator_color(grid, bg):
    """Find the color forming full-row and/or full-column separator lines."""
    H, W = len(grid), len(grid[0])
    # candidate: a color that occupies an entire row or entire column
    candidates = {}
    for r in range(H):
        vals = set(grid[r])
        if len(vals) == 1:
            v = next(iter(vals))
            if v != bg:
                candidates[v] = candidates.get(v, 0) + 1
    for c in range(W):
        vals = set(grid[r][c] for r in range(H))
        if len(vals) == 1:
            v = next(iter(vals))
            if v != bg:
                candidates[v] = candidates.get(v, 0) + 1
    if not candidates:
        return None
    return max(candidates.items(), key=lambda kv: kv[1])[0]


def _segments(is_sep, n):
    """Given booleans marking separator indices along an axis of length n,
    return list of (start, end_exclusive) panel ranges between separators."""
    segs = []
    start = None
    for i in range(n):
        if is_sep[i]:
            if start is not None:
                segs.append((start, i))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        segs.append((start, n))
    return segs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    sep = _separator_color(input_grid, bg)
    T = {}
    if sep is None:
        return T

    row_is_sep = [all(input_grid[r][c] == sep for c in range(W)) for r in range(H)]
    col_is_sep = [all(input_grid[r][c] == sep for r in range(H)) for c in range(W)]

    row_segs = _segments(row_is_sep, H)
    col_segs = _segments(col_is_sep, W)
    if not row_segs or not col_segs:
        return T

    # All panels must share the same height and width for a clean tiling.
    panel_h = row_segs[0][1] - row_segs[0][0]
    panel_w = col_segs[0][1] - col_segs[0][0]
    for (rs, re) in row_segs:
        if re - rs != panel_h:
            return T
    for (cs, ce) in col_segs:
        if ce - cs != panel_w:
            return T

    # Find the template panel: the one with the most non-background cells.
    best = None
    best_count = -1
    for (rs, re) in row_segs:
        for (cs, ce) in col_segs:
            cnt = 0
            for r in range(rs, re):
                for c in range(cs, ce):
                    if input_grid[r][c] != bg:
                        cnt += 1
            if cnt > best_count:
                best_count = cnt
                best = (rs, cs)
    if best is None or best_count <= 0:
        return T

    trs, tcs = best
    # Build the template content (relative offsets -> color, non-bg only).
    template = {}
    for dr in range(panel_h):
        for dc in range(panel_w):
            v = input_grid[trs + dr][tcs + dc]
            if v != bg:
                template[(dr, dc)] = v

    # Stamp the template into every panel (including overwriting stray cells
    # in non-template panels so they exactly match).
    for (rs, re) in row_segs:
        for (cs, ce) in col_segs:
            for dr in range(panel_h):
                for dc in range(panel_w):
                    r, c = rs + dr, cs + dc
                    want = template.get((dr, dc), bg)
                    if input_grid[r][c] != want:
                        T[(r, c)] = want
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
