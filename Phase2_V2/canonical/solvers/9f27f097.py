def infer_T(input_grid):
    """Latent transformation mask: dict {(r,c): new_color}.

    Structure: the grid contains a background color, a two-color 'pattern'
    block, and a rectangular 'hole' filled with color 0 (same size as the
    pattern). The hole is filled with the horizontal mirror (left-right flip)
    of the pattern block. T marks every hole cell with its target color.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Hole = bounding box of color-0 cells.
    hole = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 0]
    if not hole:
        return {}
    hr0 = min(r for r, c in hole); hr1 = max(r for r, c in hole)
    hc0 = min(c for r, c in hole); hc1 = max(c for r, c in hole)

    # Pattern = bounding box of cells that are neither background nor hole(0).
    pat = [(r, c) for r in range(H) for c in range(W)
           if input_grid[r][c] != bg and input_grid[r][c] != 0]
    if not pat:
        return {}
    pr0 = min(r for r, c in pat); pr1 = max(r for r, c in pat)
    pc0 = min(c for r, c in pat); pc1 = max(c for r, c in pat)

    block = [[input_grid[pr0 + i][pc0 + j] for j in range(pc1 - pc0 + 1)]
             for i in range(pr1 - pr0 + 1)]
    # Horizontal mirror (left-right flip).
    flipped = [row[::-1] for row in block]

    T = {}
    bh, bw = len(flipped), len(flipped[0])
    for i in range(min(bh, hr1 - hr0 + 1)):
        for j in range(min(bw, hc1 - hc0 + 1)):
            T[(hr0 + i, hc0 + j)] = flipped[i][j]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
