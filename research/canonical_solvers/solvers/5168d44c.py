def infer_T(input_grid):
    """Infer the latent transformation mask for puzzle 5168d44c.

    Structure: a periodic line of 3-dots (all in one row or one column,
    evenly spaced) with a 3x3 box of color-2 whose center sits on one of
    the dots. The box slides one period along the line in the increasing
    direction (down for a vertical line, right for a horizontal line),
    while the line of dots itself is preserved.

    Returns T as a dict {(r, c): new_color} of the only cells that change:
    the old box's 2-ring is reverted to its underlying line value, and the
    new box's 2-ring is painted with 2. The centers (always on dots) keep 3.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Locate the 3x3 ring of 2s -> its center.
    center = None
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if all(input_grid[r + dr][c + dc] == 2
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)):
                center = (r, c)
                break
        if center is not None:
            break
    if center is None:
        return {}

    # Collect the line of 3-dots.
    dots = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 3]
    if not dots:
        return {}

    rows = set(r for r, _ in dots)
    cols = set(c for _, c in dots)
    cr, cc = center

    if len(cols) == 1:
        # Vertical line: dots share a column; step down by the period.
        line_rows = sorted(r for r, _ in dots)
        gaps = [b - a for a, b in zip(line_rows, line_rows[1:]) if b - a > 0]
        period = min(gaps) if gaps else 1
        new_center = (cr + period, cc)
    elif len(rows) == 1:
        # Horizontal line: dots share a row; step right by the period.
        line_cols = sorted(c for _, c in dots)
        gaps = [b - a for a, b in zip(line_cols, line_cols[1:]) if b - a > 0]
        period = min(gaps) if gaps else 1
        new_center = (cr, cc + period)
    else:
        return {}

    dot_set = set(dots)
    T = {}

    # Revert the old box's 2-ring: restore underlying line value (3 on a dot,
    # else background 0).
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, ccc = cr + dr, cc + dc
            if 0 <= rr < H and 0 <= ccc < W:
                T[(rr, ccc)] = 3 if (rr, ccc) in dot_set else 0

    # Paint the new box's 2-ring (overrides any overlap with the old ring).
    ncr, ncc = new_center
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, ccc = ncr + dr, ncc + dc
            if 0 <= rr < H and 0 <= ccc < W:
                T[(rr, ccc)] = 2

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
