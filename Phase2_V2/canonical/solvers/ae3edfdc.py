def infer_T(input_grid):
    """Latent mask: clear scattered satellite markers, then draw a cross-arm of
    the satellite color adjacent to each center on every side from which an
    aligned satellite marker is visible (same row/column)."""
    H, W = len(input_grid), len(input_grid[0])
    # Each center color is paired with its satellite color: 1<->7, 2<->3.
    pair = {1: 7, 2: 3}
    centers = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W)
               if input_grid[r][c] in pair]
    T = {}
    # Erase every scattered satellite marker.
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] in (3, 7):
                T[(r, c)] = 0
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for (cr, cc, cv) in centers:
        sat = pair[cv]
        for dr, dc in dirs:
            # Scan along this direction for an aligned satellite marker.
            r, c = cr + dr, cc + dc
            found = False
            while 0 <= r < H and 0 <= c < W:
                if input_grid[r][c] == sat:
                    found = True
                    break
                r += dr
                c += dc
            if found:
                T[(cr + dr, cc + dc)] = sat
        # Preserve the center cell.
        T[(cr, cc)] = cv
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
