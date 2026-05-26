def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cr, cc = H // 2, W // 2
    sel = input_grid[cr][cc]  # selected color sits at the center cell

    # locate which quadrant the selected color occupies (its non-bg cells,
    # excluding the central cross row/col)
    cells = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] == sel and r != cr and c != cc]
    if not cells:
        return {(r, c): bg for r in range(H) for c in range(W)}
    top = sum(1 for r, c in cells if r < cr)
    bot = sum(1 for r, c in cells if r > cr)
    left = sum(1 for r, c in cells if c < cc)
    right = sum(1 for r, c in cells if c > cc)
    dr = -1 if top >= bot else 1
    dc = -1 if left >= right else 1

    # the diagonal ray cells from center into that quadrant
    diag = set()
    r, c = cr, cc
    while 0 <= r < H and 0 <= c < W:
        diag.add((r, c))
        r += dr
        c += dc

    # latent mask: every cell is overwritten -> bg everywhere except the
    # surviving diagonal, which keeps the selected color
    T = {}
    for rr in range(H):
        for ck in range(W):
            T[(rr, ck)] = sel if (rr, ck) in diag else bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
