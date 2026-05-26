def infer_T(input_grid):
    """Infer the latent fill/ray mask.

    Structure: a rectangular box drawn in a single non-background color, with a
    one-cell gap somewhere along its border. The transformation fills the box
    interior with 8 and shoots a ray of 8 outward from the gap to the grid edge.
    """
    H, W = len(input_grid), len(input_grid[0])
    out_color = 8

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    box_colors = [c for c in counts if c != bg]
    if not box_colors:
        return {}
    box = box_colors[0]

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == box]
    rmin = min(r for r, c in cells); rmax = max(r for r, c in cells)
    cmin = min(c for r, c in cells); cmax = max(c for r, c in cells)

    T = {}
    # Fill the box interior.
    for r in range(rmin + 1, rmax):
        for c in range(cmin + 1, cmax):
            if input_grid[r][c] == bg:
                T[(r, c)] = out_color

    # Locate gaps: background cells lying on the bounding-box border.
    gaps = []
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            if (r == rmin or r == rmax or c == cmin or c == cmax) and input_grid[r][c] == bg:
                gaps.append((r, c))

    # Shoot a ray outward through each gap to the grid edge.
    for (gr, gc) in gaps:
        if gr == rmin:
            dr, dc = -1, 0
        elif gr == rmax:
            dr, dc = 1, 0
        elif gc == cmin:
            dr, dc = 0, -1
        elif gc == cmax:
            dr, dc = 0, 1
        else:
            continue
        T[(gr, gc)] = out_color
        r, c = gr + dr, gc + dc
        while 0 <= r < H and 0 <= c < W:
            T[(r, c)] = out_color
            r += dr; c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
