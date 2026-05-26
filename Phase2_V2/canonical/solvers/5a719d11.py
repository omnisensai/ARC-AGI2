from collections import Counter


def _bands(grid):
    """Split grid into row/col bands separated by all-zero lines."""
    H, W = len(grid), len(grid[0])
    sep_rows = [r for r in range(H) if all(v == 0 for v in grid[r])]
    sep_cols = [c for c in range(W) if all(grid[r][c] == 0 for r in range(H))]
    rbands = []
    r = 0
    while r < H:
        if r in sep_rows:
            r += 1
            continue
        r2 = r
        while r2 < H and r2 not in sep_rows:
            r2 += 1
        rbands.append((r, r2))
        r = r2
    cbands = []
    c = 0
    while c < W:
        if c in sep_cols:
            c += 1
            continue
        c2 = c
        while c2 < W and c2 not in sep_cols:
            c2 += 1
        cbands.append((c, c2))
        c = c2
    return rbands, cbands


def _panel_info(grid, r0, r1, c0, c1):
    """Background color and set of (local r,c) shape cells for a panel."""
    cnt = Counter(grid[r][c] for r in range(r0, r1) for c in range(c0, c1))
    bg = cnt.most_common(1)[0][0]
    cells = {
        (r - r0, c - c0)
        for r in range(r0, r1)
        for c in range(c0, c1)
        if grid[r][c] != bg
    }
    return bg, cells


def infer_T(input_grid):
    """Compute a latent mask {(r,c): new_color}.

    The grid is divided into horizontal bands (separated by all-zero rows)
    and exactly two columns of panels (separated by an all-zero column).
    Within each band the LEFT and RIGHT panels swap their shape geometries:
    the destination panel keeps its own background, and the incoming shape
    is drawn using the SOURCE panel's background color. (When both panels
    share a background, the swapped shapes become background-colored and
    therefore vanish.)
    """
    rbands, cbands = _bands(input_grid)
    T = {}
    if len(cbands) != 2:
        return T
    (cL0, cL1), (cR0, cR1) = cbands[0], cbands[1]
    for (r0, r1) in rbands:
        bgL, cellsL = _panel_info(input_grid, r0, r1, cL0, cL1)
        bgR, cellsR = _panel_info(input_grid, r0, r1, cR0, cR1)
        # LEFT panel becomes RIGHT's shape, painted in RIGHT's bg color.
        for r in range(r0, r1):
            for c in range(cL0, cL1):
                lr, lc = r - r0, c - cL0
                T[(r, c)] = bgR if (lr, lc) in cellsR else bgL
        # RIGHT panel becomes LEFT's shape, painted in LEFT's bg color.
        for r in range(r0, r1):
            for c in range(cR0, cR1):
                lr, lc = r - r0, c - cR0
                T[(r, c)] = bgL if (lr, lc) in cellsL else bgR
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
