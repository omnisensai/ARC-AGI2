from collections import deque


def infer_T(input_grid):
    """Latent transformation mask: every cell -> its final color.

    Structure of the puzzle: black (0) is empty space, color 1 draws nested
    spiral / loop walls, and a handful of colored marker cells (seeds) are
    sprinkled in.  Two kinds of seeds exist:

      * wall-seeds sit ON a wall line (>=2 of their von-Neumann neighbours are
        walls, or they sit at a wall endpoint pinned against the grid border
        so wall+out-of-bounds >= 2 with at least one real wall).  They plug the
        gap in the spiral and recolour the wall stroke.
      * fill-seeds sit in open space; each one floods the open region it lives
        in once the walls (and the gap-plugging wall-seeds) are treated as
        barriers.

    Mask construction:
      1. classify seeds into wall-seeds / fill-seeds,
      2. recolour every wall cell with the colour of the nearest wall-seed
         (8-connected BFS through the wall+wall-seed structure),
      3. flood every open region (4-connected, walls as barriers) with the
         colour of the single fill-seed it contains.
    """
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    NB4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    NB8 = ((1, 0), (-1, 0), (0, 1), (0, -1),
           (1, 1), (1, -1), (-1, 1), (-1, -1))

    # --- seeds: any colour that is not background(0) and not wall(1) ---
    seeds = [(r, c, g[r][c]) for r in range(H) for c in range(W)
             if g[r][c] not in (0, 1)]

    wall_seeds, fill_seeds = [], []
    for (r, c, v) in seeds:
        wn = sum(1 for dr, dc in NB4 if inb(r + dr, c + dc) and g[r + dr][c + dc] == 1)
        oob = sum(1 for dr, dc in NB4 if not inb(r + dr, c + dc))
        if wn >= 2 or (wn >= 1 and wn + oob >= 2):
            wall_seeds.append((r, c, v))
        else:
            fill_seeds.append((r, c, v))

    # --- barrier = real walls + wall-seed cells (which plug the gaps) ---
    is_wall = [[g[r][c] == 1 for c in range(W)] for r in range(H)]
    for (r, c, v) in wall_seeds:
        is_wall[r][c] = True

    T = {}

    # --- recolour walls by nearest wall-seed (8-connected BFS) ---
    wall_color = [[None] * W for _ in range(H)]
    dq = deque()
    for (r, c, v) in wall_seeds:
        wall_color[r][c] = v
        dq.append((r, c))
    while dq:
        r, c = dq.popleft()
        for dr, dc in NB8:
            nr, nc = r + dr, c + dc
            if inb(nr, nc) and is_wall[nr][nc] and wall_color[nr][nc] is None:
                wall_color[nr][nc] = wall_color[r][c]
                dq.append((nr, nc))
    for r in range(H):
        for c in range(W):
            if is_wall[r][c] and wall_color[r][c] is not None:
                T[(r, c)] = wall_color[r][c]

    # --- flood open regions and paint each with its fill-seed colour ---
    fill_at = {(r, c): v for (r, c, v) in fill_seeds}
    seen = [[is_wall[r][c] for c in range(W)] for r in range(H)]
    for r in range(H):
        for c in range(W):
            if seen[r][c]:
                continue
            cells = []
            dq = deque([(r, c)])
            seen[r][c] = True
            while dq:
                cr, cc = dq.popleft()
                cells.append((cr, cc))
                for dr, dc in NB4:
                    nr, nc = cr + dr, cc + dc
                    if inb(nr, nc) and not seen[nr][nc]:
                        seen[nr][nc] = True
                        dq.append((nr, nc))
            colors = [fill_at[cell] for cell in cells if cell in fill_at]
            if colors:
                col = colors[0]
                for cell in cells:
                    T[cell] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
