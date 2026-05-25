"""Canonical solver for ARC puzzle 1b60fb0c.

Rule: the input contains a single shape (color 1) that is meant to be 4-fold
rotationally symmetric (90-degree rotation) about a center, but one arm/quadrant
is missing. Find the center that makes the shape rotationally consistent, take
the orbit of every shape cell under 90-degree rotation, and paint the cells that
must be added to complete the symmetry with color 2.
"""


def _rot_image_doubled(r, c, cr2, cc2):
    """90-degree rotation image of cell (r,c) in doubled-coordinate space.

    Center is at (cr2/2, cc2/2). Returns doubled coords (2*nr, 2*nc)."""
    vr = 2 * r - cr2
    vc = 2 * c - cc2
    return (-vc + cr2, vr + cc2)


def _orbit(r, c, cr2, cc2):
    """Return the 4 rotation images (0/90/180/270 deg) as integer cells, or None
    if any image does not land on an integer cell for this center."""
    pts = []
    vr = 2 * r - cr2
    vc = 2 * c - cc2
    for _ in range(4):
        cur_r = vr + cr2
        cur_c = vc + cc2
        if cur_r % 2 or cur_c % 2:
            return None
        pts.append((cur_r // 2, cur_c // 2))
        vr, vc = -vc, vr  # rotate 90 degrees
    return pts


def infer_T(input_grid):
    """Infer the latent mask: dict {(r,c): 2} of cells that complete the shape's
    4-fold rotational symmetry."""
    H = len(input_grid)
    W = len(input_grid[0])

    # The shape: every non-background cell. Background is the most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    shape = set((r, c) for r in range(H) for c in range(W)
                if input_grid[r][c] != bg)
    if not shape:
        return {}

    rs = [r for r, _ in shape]
    cs = [c for _, c in shape]

    # Find the rotation center: search half-integer centers (doubled coords) over
    # the bounding box. A valid center maps every shape cell to an integer cell
    # under 90-degree rotation; pick the one maximizing how many shape cells rotate
    # onto existing shape cells (i.e. the best-supported symmetry center).
    best_center = None
    best_score = -1
    for cr2 in range(2 * min(rs), 2 * max(rs) + 1):
        for cc2 in range(2 * min(cs), 2 * max(cs) + 1):
            valid = True
            score = 0
            for (r, c) in shape:
                rr, rcc = _rot_image_doubled(r, c, cr2, cc2)
                if rr % 2 or rcc % 2:
                    valid = False
                    break
                if (rr // 2, rcc // 2) in shape:
                    score += 1
            if valid and score > best_score:
                best_score = score
                best_center = (cr2, cc2)

    if best_center is None:
        return {}

    cr2, cc2 = best_center

    # Complete the shape: union of every shape cell's rotational orbit.
    full = set()
    for (r, c) in shape:
        orb = _orbit(r, c, cr2, cc2)
        if orb is None:
            continue
        for q in orb:
            full.add(q)

    # The mask is the set of newly added cells (within bounds), painted color 2.
    T = {}
    for (r, c) in full - shape:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
