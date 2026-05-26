def infer_T(input_grid):
    """Infer the latent mask {(r,c): new_color}.

    The grid is a tiling of 3x3 cells (colors 0/1) separated by lines of color 4.
    One special 6x6 'key' block holds a marker color (not 0/1/4) painted at the
    centers of 2x2 super-pixels, encoding a 3x3 target pattern. Every ordinary
    3x3 cell whose set of 1-cells is a superset of that target pattern has its
    target positions recolored to the marker color.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Identify the marker color (anything other than 0, 1, 4).
    marker = None
    for row in input_grid:
        for v in row:
            if v not in (0, 1, 4):
                marker = v
                break
        if marker is not None:
            break

    T = {}
    if marker is None:
        return T

    # Locate the marker's bounding box; the key block top-left starts there.
    coords = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == marker]
    r0 = min(r for r, c in coords)
    c0 = min(c for r, c in coords)

    # Read the 3x3 target pattern from the 2x2 super-pixels of the key block.
    target = set()
    for pr in range(3):
        for pc in range(3):
            rr, cc = r0 + 2 * pr, c0 + 2 * pc
            if 0 <= rr < H and 0 <= cc < W and input_grid[rr][cc] == marker:
                target.add((pr, pc))

    # Scan all aligned 3x3 cells; recolor those that contain the full target.
    r = 0
    while r + 3 <= H:
        c = 0
        while c + 3 <= W:
            block = [[input_grid[r + dr][c + dc] for dc in range(3)] for dr in range(3)]
            flat = [x for rowb in block for x in rowb]
            if 4 not in flat:  # a genuine 0/1 cell, not a separator/key region
                ones = set((dr, dc) for dr in range(3) for dc in range(3)
                           if block[dr][dc] == 1)
                if target and target <= ones:
                    for (dr, dc) in target:
                        T[(r + dr, c + dc)] = marker
            c += 4
        r += 4

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
