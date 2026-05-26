"""Canonical latent-T solver for ARC puzzle c6e1b8da.

Rule (inferred from input structure):
  The grid contains several solid colored rectangles that overlap.  Each
  rectangle is either a STAYER or a MOVER:
    * A MOVER carries a one-cell-wide "arm" (a thin line protruding from one
      edge of its solid body).  The rectangle's body slides in the arm's
      direction by the arm's length; the arm itself disappears.
    * A STAYER has no arm.  Part of it may be hidden behind another
      rectangle (an occlusion bite); it is redrawn as its full bounding-box
      rectangle, completing the hidden part.
  Movers are painted on top of stayers (the moving rectangle occludes
  whatever it lands on).

infer_T computes, from the input alone, the rendered target and returns the
latent mask of cells whose color changes.  apply_T overwrites only those
cells.
"""


def _components(g):
    """Connected components (4-connectivity) of equal nonzero color."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v == 0 or seen[r][c]:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if a < 0 or a >= H or b < 0 or b >= W:
                    continue
                if seen[a][b] or g[a][b] != v:
                    continue
                seen[a][b] = True
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((a + dr, b + dc))
            out.append((v, cells))
    return out


def _classify(g, cells, v):
    """Return (kind, dr, dc, length, body_box).

    kind is 'mover' (has a genuine arm) or 'stayer'.  body_box is the solid
    rectangle to redraw (for a stayer it is the full bounding box).
    """
    cs = set(cells)
    rs = [r for r, _ in cells]
    co = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(co), max(co)
    BH, BW = r1 - r0 + 1, c1 - c0 + 1
    rowcount = [sum(1 for c in range(c0, c1 + 1) if (r, c) in cs)
                for r in range(r0, r1 + 1)]
    colcount = [sum(1 for r in range(r0, r1 + 1) if (r, c) in cs)
                for c in range(c0, c1 + 1)]

    # Candidate one-cell-wide edge strips (rows/cols at a border with count 1).
    cands = []  # (dr, dc, length, strip_region, body_box)
    k = 0
    while k < BH and rowcount[k] == 1:
        k += 1
    if 0 < k < BH:
        region = [(r, c) for r in range(r0, r0 + k) for c in range(c0, c1 + 1)]
        cands.append((-1, 0, k, region, (r0 + k, r1, c0, c1)))
    k = 0
    while k < BH and rowcount[BH - 1 - k] == 1:
        k += 1
    if 0 < k < BH:
        region = [(r, c) for r in range(r1 - k + 1, r1 + 1)
                  for c in range(c0, c1 + 1)]
        cands.append((1, 0, k, region, (r0, r1 - k, c0, c1)))
    k = 0
    while k < BW and colcount[k] == 1:
        k += 1
    if 0 < k < BW:
        region = [(r, c) for c in range(c0, c0 + k) for r in range(r0, r1 + 1)]
        cands.append((0, -1, k, region, (r0, r1, c0 + k, c1)))
    k = 0
    while k < BW and colcount[BW - 1 - k] == 1:
        k += 1
    if 0 < k < BW:
        region = [(r, c) for c in range(c1 - k + 1, c1 + 1)
                  for r in range(r0, r1 + 1)]
        cands.append((0, 1, k, region, (r0, r1, c0, c1 - k)))

    for dr, dc, length, region, body in cands:
        # The strip's non-self cells form the "gap".  If the gap is entirely a
        # single other (non-background) color, the strip is just a sliver of an
        # occluded rectangle (occlusion) -- not an arm.  Otherwise it is a
        # genuine protruding arm and the shape is a mover.
        gap_colors = set()
        gap = 0
        for (r, c) in region:
            if (r, c) in cs:
                continue
            gap += 1
            gap_colors.add(g[r][c])
        if gap > 0 and 0 not in gap_colors and len(gap_colors) == 1:
            continue  # occlusion sliver -> not an arm; try next candidate
        return ('mover', dr, dc, length, body)

    return ('stayer', 0, 0, 0, (r0, r1, c0, c1))


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    g = input_grid
    H, W = len(g), len(g[0])

    rendered = [[0] * W for _ in range(H)]
    stayers, movers = [], []
    for v, cells in _components(g):
        kind, dr, dc, length, (br0, br1, bc0, bc1) = _classify(g, cells, v)
        if kind == 'mover':
            movers.append((br0 + dr * length, br1 + dr * length,
                           bc0 + dc * length, bc1 + dc * length, v))
        else:
            stayers.append((br0, br1, bc0, bc1, v))

    # Paint stayers first, then movers on top (a moving rectangle occludes
    # whatever it lands on).
    for r0, r1, c0, c1, v in stayers + movers:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if 0 <= r < H and 0 <= c < W:
                    rendered[r][c] = v

    T = {}
    for r in range(H):
        for c in range(W):
            if rendered[r][c] != g[r][c]:
                T[(r, c)] = rendered[r][c]
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
