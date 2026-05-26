def infer_T(input_grid):
    """Infer the latent transformation mask.

    The input is a regular lattice of 5-blocks separated by gap rows/cols of 0.
    A gap line (row or column) that lies strictly *between* two block lines is an
    "active" line. Inside the block bounding box every cell on an active line is
    painted 2; where an active line extends out into the border gap region beyond
    the bounding box it is painted 1.
    """
    H, W = len(input_grid), len(input_grid[0])

    block_rows = [r for r in range(H) if any(v == 5 for v in input_grid[r])]
    block_cols = [c for c in range(W) if any(input_grid[r][c] == 5 for r in range(H))]
    T = {}
    if not block_rows or not block_cols:
        return T

    rmin, rmax = min(block_rows), max(block_rows)
    cmin, cmax = min(block_cols), max(block_cols)
    brows = set(block_rows)
    bcols = set(block_cols)

    # Interior gap lines: gap rows/cols sandwiched between block lines.
    interior_rows = set(r for r in range(H) if r not in brows and rmin < r < rmax)
    interior_cols = set(c for c in range(W) if c not in bcols and cmin < c < cmax)

    for r in range(H):
        for c in range(W):
            on_line = (r in interior_rows) or (c in interior_cols)
            if not on_line:
                continue
            in_box = (rmin <= r <= rmax) and (cmin <= c <= cmax)
            T[(r, c)] = 2 if in_box else 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
