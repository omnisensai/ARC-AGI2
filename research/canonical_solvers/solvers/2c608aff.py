def infer_T(input_grid):
    """Compute a latent dict mask {(r,c): color} of ray cells.

    Structure: a background, one large solid rectangle, and scattered
    single-cell markers. Every marker that is row- or column-aligned with the
    rectangle's span shoots a ray (in its own color) from itself up to the
    rectangle's nearest edge (marker inclusive, rectangle exclusive). Markers
    not aligned with the rectangle are left untouched.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # 4-connected components of non-background cells
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or seen[r][c]:
                continue
            color = input_grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if seen[rr][cc] or input_grid[rr][cc] != color:
                    continue
                seen[rr][cc] = True
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))
            comps.append((color, cells))

    T = {}
    if not comps:
        return T

    # the rectangle is the largest component
    rect_idx = max(range(len(comps)), key=lambda i: len(comps[i][1]))
    rect_cells = comps[rect_idx][1]
    rmin = min(r for r, _ in rect_cells)
    rmax = max(r for r, _ in rect_cells)
    cmin = min(c for _, c in rect_cells)
    cmax = max(c for _, c in rect_cells)

    for idx, (color, cells) in enumerate(comps):
        if idx == rect_idx or len(cells) != 1:
            continue
        mr, mc = cells[0]
        if cmin <= mc <= cmax:
            # vertical ray toward the rectangle
            if mr < rmin:
                for rr in range(mr, rmin):
                    T[(rr, mc)] = color
            elif mr > rmax:
                for rr in range(rmax + 1, mr + 1):
                    T[(rr, mc)] = color
        elif rmin <= mr <= rmax:
            # horizontal ray toward the rectangle
            if mc < cmin:
                for cc in range(mc, cmin):
                    T[(mr, cc)] = color
            elif mc > cmax:
                for cc in range(cmax + 1, mc + 1):
                    T[(mr, cc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
