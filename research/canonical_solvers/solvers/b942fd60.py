"""Canonical latent-T solver for ARC puzzle b942fd60.

Rule (ray / line tracing):
  A single seed cell of color 2 sits on a grid edge.  It emits a ray of 2s
  travelling into the grid (perpendicular to that edge).  A ray advances over
  background cells until the next cell ahead is a colored marker (3/6/7/8) or
  the grid edge:
    * if the next cell is a marker, the ray stops on the cell just before it;
      that stop cell is a "turn point" that emits two fresh rays in the two
      perpendicular directions (a growing tree of 2-lines);
    * if the ray runs off the grid edge it simply terminates (no turn).
  Markers and edges block rays.  Rays pass over crossings of already-drawn
  lines, but a perpendicular branch is NOT spawned into a direction whose first
  step is already painted (a crossing is traversed, not re-split).
  The latent mask is the set of background cells the trace covers, painted 2.
"""

MARKERS = (3, 6, 7, 8)
PERP = {(0, 1): ((1, 0), (-1, 0)), (0, -1): ((1, 0), (-1, 0)),
        (1, 0): ((0, 1), (0, -1)), (-1, 0): ((0, 1), (0, -1))}


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _seed(grid):
    H, W = len(grid), len(grid[0])
    found = None
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 2:
                found = (r, c)
    return found


def _seed_dir(seed, H, W):
    r, c = seed
    if c == 0:
        return (0, 1)
    if c == W - 1:
        return (0, -1)
    if r == 0:
        return (1, 0)
    if r == H - 1:
        return (-1, 0)
    # interior seed: emit toward the nearest edge horizontally as a fallback.
    return (0, 1)


def _run_ray(grid, H, W, r, c, dr, dc):
    """Trace a ray from (r,c) in direction (dr,dc).

    Returns (cells_covered, end_type, turn_point) where end_type is
    'marker' or 'edge' and turn_point is the last cell before the blocker.
    """
    cells = [(r, c)]
    cr, cc = r, c
    while True:
        nr, nc = cr + dr, cc + dc
        if not (0 <= nr < H and 0 <= nc < W):
            return cells, 'edge', (cr, cc)
        if grid[nr][nc] in MARKERS:
            return cells, 'marker', (cr, cc)
        cr, cc = nr, nc
        cells.append((cr, cc))


def infer_T(input_grid):
    """Infer the latent transformation mask (set of cells to paint 2)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    seed = _seed(input_grid)
    mask = set()
    if seed is None:
        return mask

    d0 = _seed_dir(seed, H, W)
    queue = [(seed[0], seed[1], d0[0], d0[1])]
    processed = set()
    painted = set()

    while queue:
        r, c, dr, dc = queue.pop(0)
        key = (r, c, dr, dc)
        if key in processed:
            continue
        processed.add(key)

        cells, end_type, tp = _run_ray(input_grid, H, W, r, c, dr, dc)
        for cell in cells:
            painted.add(cell)

        # Only marker-blocked stops spawn perpendicular rays.
        if end_type != 'marker':
            continue
        tr, tc = tp
        for pdr, pdc in PERP[(dr, dc)]:
            nxt = (tr + pdr, tc + pdc)
            # Do not re-split into a direction that immediately enters an
            # already-painted line (rays pass over crossings, they do not
            # spawn a new branch at a crossing).
            if 0 <= nxt[0] < H and 0 <= nxt[1] < W and nxt in painted:
                continue
            queue.append((tr, tc, pdr, pdc))

    # The mask paints only background cells that the trace covers.
    for (r, c) in painted:
        if input_grid[r][c] == bg:
            mask.add((r, c))
    return mask


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells with color 2."""
    out = [row[:] for row in input_grid]
    for (r, c) in T:
        out[r][c] = 2
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
