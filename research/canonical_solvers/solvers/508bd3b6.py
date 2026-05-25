def infer_T(input_grid):
    """Trace the diagonal ray emitted from the 8-line tip; bounce off the 2-wall.

    Structure: a short diagonal line of 8s defines a direction; a solid block of
    2s is a wall. A ray of 3s continues from the leading tip of the 8-line in the
    same diagonal direction, reflecting off the wall (flip the blocked axis).
    Returns a latent mask {(r,c): 3}.
    """
    H, W = len(input_grid), len(input_grid[0])
    eights = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    eset = set(eights)
    wall = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2)

    def diag_neighbors(r, c):
        ns = []
        for dr in (-1, 1):
            for dc in (-1, 1):
                if (r + dr, c + dc) in eset:
                    ns.append((dr, dc))
        return ns

    # Endpoints of the diagonal line have exactly one diagonal neighbour.
    endpoints = [(r, c) for (r, c) in eights if len(diag_neighbors(r, c)) == 1]

    # Each endpoint's outward direction = opposite of its neighbour direction.
    candidates = []
    for (r, c) in endpoints:
        ndr, ndc = diag_neighbors(r, c)[0]
        candidates.append(((r, c), (-ndr, -ndc)))

    # Pick the tip whose immediate outward cell is empty open space.
    chosen = None
    for (tip, (dr, dc)) in candidates:
        nr, nc = tip[0] + dr, tip[1] + dc
        if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in wall and input_grid[nr][nc] == 0:
            chosen = (tip, (dr, dc))
            break
    if chosen is None:
        chosen = candidates[0]
    (tip, (dr, dc)) = chosen

    T = {}
    r, c = tip
    while True:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < H and 0 <= nc < W):
            break
        if (nr, nc) in wall:
            # Reflect: flip the axis that is blocked by the wall (or both at a corner).
            block_v = (r + dr, c) in wall or not (0 <= r + dr < H)
            block_h = (r, c + dc) in wall or not (0 <= c + dc < W)
            if block_v and not block_h:
                dr = -dr
            elif block_h and not block_v:
                dc = -dc
            else:
                dr, dc = -dr, -dc
            continue
        T[(nr, nc)] = 3
        r, c = nr, nc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
