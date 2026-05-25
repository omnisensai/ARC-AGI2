def infer_T(input_grid):
    """Infer the latent fill/ray mask.

    Each box is a hollow rectangle outline of 1s. Its interior is filled with
    8. If the outline has a gap (a single missing 1 on the rectangle border),
    an 8-ray shoots outward from that gap (perpendicular to the edge) all the
    way to the grid border; closed boxes get no ray.
    """
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid
    BOX, FILL = 1, 8

    # 4-connected components of box-color cells
    seen = [[False]*W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == BOX and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == BOX and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    T = {}
    for cells in comps:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue  # too small to be a box

        # fill interior
        for ir in range(r0 + 1, r1):
            for ic in range(c0 + 1, c1):
                T[(ir, ic)] = FILL

        # detect gaps on the bounding rectangle border; ray direction is outward
        gaps = []
        for ic in range(c0, c1 + 1):
            if g[r0][ic] != BOX:
                gaps.append((r0, ic, -1, 0))   # top edge -> upward
            if g[r1][ic] != BOX:
                gaps.append((r1, ic, 1, 0))    # bottom edge -> downward
        for ir in range(r0 + 1, r1):
            if g[ir][c0] != BOX:
                gaps.append((ir, c0, 0, -1))   # left edge -> leftward
            if g[ir][c1] != BOX:
                gaps.append((ir, c1, 0, 1))    # right edge -> rightward

        for (gr, gc, dr, dc) in gaps:
            rr, cc = gr, gc
            while 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = FILL
                rr += dr
                cc += dc

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
