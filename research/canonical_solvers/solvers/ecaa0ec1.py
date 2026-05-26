"""Canonical latent-T solver for ARC puzzle ecaa0ec1.

Structure of every input:
  * one 3x3 block made of colors {1, 8} sitting somewhere on a 0 background;
  * four single-cell markers of color 4. Three of them form a right-angle
    "L" (occupying three corners of a 3x3 bounding box); the fourth marker
    is isolated.

Transformation:
  * The block is rotated in place. The rotation is the one that carries the
    isolated marker's diagonal corner (relative to the block) onto the L's
    diagonal corner (the centre of the L's 3x3 bounding box, which is itself
    a diagonal corner of the block).
  * All four input markers are erased; a single color-4 marker is placed at
    the centre of the L's bounding box.

infer_T builds a {(r,c): color} mask of every cell that changes; apply_T
overwrites only those cells on a copy of the input.
"""


def _components(grid, colors):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if seen[r][c] or grid[r][c] not in colors:
                continue
            stack = [(r, c)]
            cells = []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] \
                                and grid[nr][nc] in colors:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _rotate_ccw(mat, steps):
    """Rotate a square matrix 90*steps degrees counter-clockwise."""
    m = [row[:] for row in mat]
    for _ in range(steps % 4):
        n = len(m)
        m = [[m[j][n - 1 - i] for j in range(n)] for i in range(n)]
    return m


# corner ordering used to measure rotation: counter-clockwise cycle
_CCW = ["TL", "BL", "BR", "TR"]


def _corner_name(dr, dc):
    return ("T" if dr < 0 else "B") + ("L" if dc < 0 else "R")


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    # 1. locate the 3x3 block of colors 1/8.
    block_cells = [(r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] in (1, 8)]
    if not block_cells:
        return T
    br0, br1, bc0, bc1 = _bbox(block_cells)
    block = [[input_grid[r][c] for c in range(bc0, bc1 + 1)]
             for r in range(br0, br1 + 1)]
    bcr = (br0 + br1) / 2.0
    bcc = (bc0 + bc1) / 2.0

    # 2. locate the four color-4 markers; split into the L-cluster of three
    #    and the isolated one (largest total Manhattan distance to the rest).
    fours = [(r, c) for r in range(H) for c in range(W)
             if input_grid[r][c] == 4]
    if len(fours) != 4:
        return T

    def total_dist(p):
        return sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in fours)

    iso = max(fours, key=total_dist)
    group = [p for p in fours if p != iso]

    # 3. centre of the L's bounding box (= a diagonal corner of the block).
    gr0, gr1, gc0, gc1 = _bbox(group)
    lcr = (gr0 + gr1) // 2
    lcc = (gc0 + gc1) // 2

    iso_corner = _corner_name(iso[0] - bcr, iso[1] - bcc)
    l_corner = _corner_name((gr0 + gr1) / 2.0 - bcr, (gc0 + gc1) / 2.0 - bcc)

    # 4. rotation (in CCW quarter turns) mapping iso corner -> L corner.
    steps = (_CCW.index(l_corner) - _CCW.index(iso_corner)) % 4
    rotated = _rotate_ccw(block, steps)

    # 5. build the change mask.
    #    erase old markers.
    for (r, c) in fours:
        T[(r, c)] = 0
    #    write rotated block into the same bounding box.
    for i in range(len(rotated)):
        for j in range(len(rotated[0])):
            T[(br0 + i, bc0 + j)] = rotated[i][j]
    #    place the single surviving marker at the L's centre.
    T[(lcr, lcc)] = 4

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
