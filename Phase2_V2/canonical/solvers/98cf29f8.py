def _components_by_color(grid):
    """Map each non-background color to the list of its cells."""
    H, W = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    res = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != bg:
                res.setdefault(v, []).append((r, c))
    return res, bg


def _bbox(cells):
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _largest_solid_rect(cells):
    """Largest axis-aligned fully-filled rectangle made of the given cells."""
    pts = set(cells)
    r0b, r1b, c0b, c1b = _bbox(cells)
    best = None
    best_area = 0
    for r0 in range(r0b, r1b + 1):
        for r1 in range(r0, r1b + 1):
            for c0 in range(c0b, c1b + 1):
                for c1 in range(c0, c1b + 1):
                    if all((r, c) in pts
                           for r in range(r0, r1 + 1)
                           for c in range(c0, c1 + 1)):
                        a = (r1 - r0 + 1) * (c1 - c0 + 1)
                        if a > best_area:
                            best_area = a
                            best = (r0, r1, c0, c1)
    return best


def infer_T(input_grid):
    """Latent mask {(r,c): color}.

    The grid holds two objects of distinct colors:
      - a TARGET: a solid (perfectly filled) rectangle, which never moves.
      - a MOVER: a solid 'head' rectangle plus a thin 1-wide 'arm' that points
        toward the target.
    The mover's head slides along the arm direction until its leading edge is
    adjacent to the target; the arm is erased. The mask records every cell that
    changes: erased arm cells -> background, new head cells -> mover color.
    """
    H, W = len(input_grid), len(input_grid[0])
    comps, bg = _components_by_color(input_grid)

    target_box = None
    mover_color = None
    mover_cells = None
    for color, cells in comps.items():
        r0, r1, c0, c1 = _bbox(cells)
        if len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1):
            target_box = (r0, r1, c0, c1)
        else:
            mover_color = color
            mover_cells = cells

    T = {}
    if target_box is None or mover_cells is None:
        return T

    tr0, tr1, tc0, tc1 = target_box
    hr0, hr1, hc0, hc1 = _largest_solid_rect(mover_cells)
    hh = hr1 - hr0 + 1
    hw = hc1 - hc0 + 1

    # Center of head vs center of target tells us the cardinal slide direction.
    hcr, hcc = (hr0 + hr1) / 2.0, (hc0 + hc1) / 2.0
    tcr, tcc = (tr0 + tr1) / 2.0, (tc0 + tc1) / 2.0

    if abs(tcc - hcc) >= abs(tcr - hcr):
        # horizontal move; rows stay fixed
        nr0, nr1 = hr0, hr1
        if tcc > hcc:           # target to the right
            nc1 = tc0 - 1
            nc0 = nc1 - hw + 1
        else:                   # target to the left
            nc0 = tc1 + 1
            nc1 = nc0 + hw - 1
    else:
        # vertical move; cols stay fixed
        nc0, nc1 = hc0, hc1
        if tcr > hcr:           # target below
            nr1 = tr0 - 1
            nr0 = nr1 - hh + 1
        else:                   # target above
            nr0 = tr1 + 1
            nr1 = nr0 + hh - 1

    # Erase the whole mover (head + arm).
    for (r, c) in mover_cells:
        T[(r, c)] = bg
    # Draw the head in its new position.
    for r in range(nr0, nr1 + 1):
        for c in range(nc0, nc1 + 1):
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = mover_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
