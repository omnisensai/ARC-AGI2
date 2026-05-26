def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure: a 4-colored shape and a 6-colored 'arrow' (a plus/T whose one
    arm extends two cells = the long arm). The 4-shape is reflected across the
    edge of its bounding box; the reflection direction is the long-arm
    direction rotated 90 degrees counter-clockwise. The 6-arrow is erased.
    """
    H, W = len(input_grid), len(input_grid[0])
    four = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    six = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    T = {}
    if not four or not six:
        return T
    sixset = set(six)

    # arrow center: the 6-cell with the most orthogonal 6-neighbors
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    center = None
    best = -1
    for (r, c) in six:
        nb = sum(1 for dr, dc in dirs if (r + dr, c + dc) in sixset)
        if nb > best:
            best = nb
            center = (r, c)

    # measure each arm length from the center
    armlen = {}
    for dr, dc in dirs:
        L = 0
        r, c = center
        while (r + dr, c + dc) in sixset:
            L += 1
            r += dr
            c += dc
        armlen[(dr, dc)] = L
    longarm = max(armlen, key=lambda d: armlen[d])

    # reflection direction = long arm rotated 90 deg counter-clockwise
    rdr, rdc = (-longarm[1], longarm[0])

    rs = [r for r, c in four]
    cs = [c for r, c in four]
    rmin, rmax, cmin, cmax = min(rs), max(rs), min(cs), max(cs)

    # reflect the 4-shape across the bbox edge on the reflection side
    if rdr != 0:
        axis2 = (2 * rmax + 1) if rdr > 0 else (2 * rmin - 1)
        reflected = [(axis2 - r, c) for r, c in four]
    else:
        axis2 = (2 * cmax + 1) if rdc > 0 else (2 * cmin - 1)
        reflected = [(r, axis2 - c) for r, c in four]

    reflset = set()
    for (r, c) in reflected:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 4
            reflset.add((r, c))

    # erase the arrow, but keep any cell where a reflected 4 landed
    for (r, c) in six:
        if (r, c) not in reflset:
            T[(r, c)] = 0

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
