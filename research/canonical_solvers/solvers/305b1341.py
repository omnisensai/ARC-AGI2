def infer_T(input_grid):
    """Infer a latent mask {(r,c): new_color}.

    Structure of the input:
      - A small legend in the top-left (columns 0-1, contiguous rows from the
        top) mapping each dot color -> a frame color.
      - Several scattered "dot grids": clusters of same-colored cells spaced 2
        apart.
    Each dot grid is enclosed by a frame: its bounding box, expanded by one
    cell on every side, is painted with the frame color, and the original dot
    cells are restored on top. The legend itself is cleared. When frames
    overlap, the smaller (inner) frame is painted last so it wins.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # --- read the legend (contiguous rows from row 0 with cols 0 and 1 set) ---
    legrows = []
    r = 0
    while r < H and input_grid[r][0] != 0 and input_grid[r][1] != 0:
        legrows.append(r)
        r += 1
    legend = {input_grid[r][0]: input_grid[r][1] for r in legrows}
    legset = set((r, c) for r in legrows for c in (0, 1))

    # --- remaining nonzero cells = dot grids ---
    cells = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] != 0 and (r, c) not in legset]
    cellset = set(cells)

    # cluster same-colored cells that are within chebyshev distance 2
    seen = set()
    clusters = []
    for (r, c) in cells:
        if (r, c) in seen:
            continue
        col = input_grid[r][c]
        stack = [(r, c)]
        comp = []
        while stack:
            a, b = stack.pop()
            if (a, b) in seen:
                continue
            seen.add((a, b))
            comp.append((a, b))
            for da in range(-2, 3):
                for db in range(-2, 3):
                    nb = (a + da, b + db)
                    if nb in cellset and nb not in seen and input_grid[nb[0]][nb[1]] == col:
                        stack.append(nb)
        clusters.append((col, comp))

    # compute expanded bounding box per cluster
    info = []
    for col, comp in clusters:
        rs = [a for a, b in comp]
        cs = [b for a, b in comp]
        er0, er1 = min(rs) - 1, max(rs) + 1
        ec0, ec1 = min(cs) - 1, max(cs) + 1
        area = (er1 - er0 + 1) * (ec1 - ec0 + 1)
        info.append((area, col, comp, er0, er1, ec0, ec1))
    # paint larger boxes first so smaller (inner) frames win on overlap
    info.sort(key=lambda x: -x[0])

    T = {}
    for (r, c) in legset:
        T[(r, c)] = 0
    for area, col, comp, er0, er1, ec0, ec1 in info:
        frame = legend.get(col, col)
        compset = set(comp)
        for rr in range(max(0, er0), min(H, er1 + 1)):
            for cc in range(max(0, ec0), min(W, ec1 + 1)):
                T[(rr, cc)] = col if (rr, cc) in compset else frame
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
