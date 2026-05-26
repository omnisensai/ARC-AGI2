def infer_T(input_grid):
    """Latent mask: for each '1' rectangle-outline box with a single gap, fill
    the interior with 2, fill the gap cell with 2, and shoot a 2-ray outward
    (perpendicular to the breached wall) to the grid edge."""
    H, W = len(input_grid), len(input_grid[0])
    BOX = 1
    FILL = 2

    # connected components of BOX cells (4-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == BOX and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                                and input_grid[nr][nc] == BOX):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    T = {}
    for cells in comps:
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        cellset = set(cells)

        # full bounding-rectangle border positions
        border = set()
        for c in range(c0, c1 + 1):
            border.add((r0, c))
            border.add((r1, c))
        for r in range(r0, r1 + 1):
            border.add((r, c0))
            border.add((r, c1))

        # gaps = border cells missing from this box outline
        gaps = [p for p in border if p not in cellset]

        # fill interior
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                T[(r, c)] = FILL

        # for each gap: fill it and project a ray outward to the grid edge
        for (gr, gc) in gaps:
            T[(gr, gc)] = FILL
            dr = dc = 0
            if gr == r0:
                dr = -1
            elif gr == r1:
                dr = 1
            elif gc == c0:
                dc = -1
            elif gc == c1:
                dc = 1
            if dr == 0 and dc == 0:
                continue
            nr, nc = gr + dr, gc + dc
            while 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = FILL
                nr += dr
                nc += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
