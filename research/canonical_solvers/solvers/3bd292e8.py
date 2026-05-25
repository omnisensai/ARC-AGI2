def infer_T(input_grid):
    """
    The cells of color 2 form one or more orthogonal staircase walls whose
    endpoints all land on the grid border. These walls partition the non-2
    background into connected regions. Regions that are separated by a single
    wall belong to opposite classes of a (bipartite) two-coloring. One class is
    recolored 3, the other 5. The anchor: the region containing the bottom-left
    corner cell is always color 5; the alternating two-coloring then fixes the
    rest. T is the latent mask {(r,c): new_color} over every non-2 cell.
    """
    H, W = len(input_grid), len(input_grid[0])
    WALL = 2

    # 1) Connected components (4-conn) of non-wall background cells = regions.
    region_of = {}
    regions = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == WALL or (r, c) in region_of:
                continue
            idx = len(regions)
            comp = []
            stack = [(r, c)]
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                if (rr, cc) in region_of or input_grid[rr][cc] == WALL:
                    continue
                region_of[(rr, cc)] = idx
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((rr + dr, cc + dc))
            regions.append(comp)

    n = len(regions)
    if n == 0:
        return {}

    # 2) Adjacency: two regions are wall-adjacent if a single wall cell sits
    #    directly between them (opposite cells across the wall, vertically or
    #    horizontally) belong to different regions.
    adj = {i: set() for i in range(n)}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != WALL:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                a = (r - dr, c - dc)
                b = (r + dr, c + dc)
                ra = region_of.get(a)
                rb = region_of.get(b)
                if ra is not None and rb is not None and ra != rb:
                    adj[ra].add(rb)
                    adj[rb].add(ra)

    # 3) Bipartite two-coloring (class 0 / 1) of the region adjacency graph.
    cls = {}
    for s in range(n):
        if s in cls:
            continue
        cls[s] = 0
        stack = [s]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in cls:
                    cls[y] = 1 - cls[x]
                    stack.append(y)

    # 4) Anchor: the region containing the bottom-left corner cell is color 5.
    #    Find the nearest non-wall cell to (H-1, 0) along the bottom/left border
    #    as a robust fallback if the exact corner is a wall.
    anchor_region = region_of.get((H - 1, 0))
    if anchor_region is None:
        # search bottom row then left column for first non-wall border cell
        for c in range(W):
            if (H - 1, c) in region_of:
                anchor_region = region_of[(H - 1, c)]
                break
        if anchor_region is None:
            for r in range(H - 1, -1, -1):
                if (r, 0) in region_of:
                    anchor_region = region_of[(r, 0)]
                    break
    if anchor_region is None:
        anchor_region = 0

    anchor_class = cls[anchor_region]
    color_of_class = {anchor_class: 5, 1 - anchor_class: 3}

    # 5) Build the latent mask: every non-wall cell gets its class color.
    T = {}
    for (r, c), idx in region_of.items():
        T[(r, c)] = color_of_class[cls[idx]]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
