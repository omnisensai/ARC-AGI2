def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Find connected components of border color (2 = the box-drawing color).
    # The box color is the non-bg color forming hollow rectangles.
    # Identify all colors that are not bg; pick the box color as the one with most cells.
    nonbg = {c: n for c, n in counts.items() if c != bg}
    box_color = max(nonbg, key=nonbg.get) if nonbg else None

    T = {}  # latent mask: (r,c) -> new_color
    if box_color is None:
        return T

    # Find connected components of box_color (4-connectivity)
    seen = [[False] * W for _ in range(H)]
    boxes = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == box_color and not seen[r][c]:
                stack = [(r, c)]
                comp = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] \
                                and input_grid[nr][nc] == box_color:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                boxes.append(comp)

    # color map by interior side length
    color_by_interior = {3: 8, 5: 4, 7: 3}

    for comp in boxes:
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # interior is the bounding box minus the 1-cell border frame
        ih = (r1 - r0 - 1)
        iw = (c1 - c0 - 1)
        if ih <= 0 or iw <= 0:
            continue
        # must be a frame: top/bottom rows and left/right cols are full box_color
        is_frame = True
        for cc in range(c0, c1 + 1):
            if input_grid[r0][cc] != box_color or input_grid[r1][cc] != box_color:
                is_frame = False
                break
        if is_frame:
            for rr in range(r0, r1 + 1):
                if input_grid[rr][c0] != box_color or input_grid[rr][c1] != box_color:
                    is_frame = False
                    break
        if not is_frame:
            continue
        side = min(ih, iw)
        fill = color_by_interior.get(side)
        if fill is None:
            continue
        # fill interior bg cells (leave the isolated interior marker as-is)
        for rr in range(r0 + 1, r1):
            for cc in range(c0 + 1, c1):
                if input_grid[rr][cc] == bg:
                    T[(rr, cc)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
