def infer_T(input_grid):
    """Infer a latent mask {(r,c): color} of cells to paint.

    Structure: one 2x2 core block of a single non-background color, plus a few
    single "arm" cells each sitting diagonally adjacent to one corner of the
    block. The rule extends each arm into a full diagonal ray (same diagonal
    direction, away from the block) until it leaves the grid.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    color = next((v for v in counts if v != bg), None)
    T = {}
    if color is None:
        return T, bg

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == color]

    # Locate the 2x2 core block (top-left of any all-color 2x2 window).
    block_cells = set()
    for (r, c) in cells:
        if (r + 1 < H and c + 1 < W and
                input_grid[r][c] == color and input_grid[r][c + 1] == color and
                input_grid[r + 1][c] == color and input_grid[r + 1][c + 1] == color):
            block_cells.update({(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)})
    if not block_cells:
        return T, bg

    rmin = min(r for r, c in block_cells)
    rmax = max(r for r, c in block_cells)
    cmin = min(c for r, c in block_cells)
    cmax = max(c for r, c in block_cells)

    # Arms = color cells not part of the block.
    arms = [(r, c) for (r, c) in cells if (r, c) not in block_cells]

    # Each block corner has an outward diagonal direction.
    corners = {
        (rmin, cmin): (-1, -1),
        (rmin, cmax): (-1, 1),
        (rmax, cmin): (1, -1),
        (rmax, cmax): (1, 1),
    }

    for (ar, ac) in arms:
        dir_used = None
        for (cr, cc), (dr, dc) in corners.items():
            if ar == cr + dr and ac == cc + dc:
                dir_used = (dr, dc)
                break
        if dir_used is None:
            continue
        dr, dc = dir_used
        r, c = ar + dr, ac + dc
        while 0 <= r < H and 0 <= c < W:
            T[(r, c)] = color
            r += dr
            c += dc
    return T, bg


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    mask, _bg = T
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
