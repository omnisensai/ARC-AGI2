"""Canonical latent-T solver for ARC puzzle dd6b8c4b.

Structure of every pair:
  * A "background"/wall color (6) builds a maze of rooms/rings around a small
    3x3 box made of a border color (3) with a single center marker (2).
  * Scattered single-cell markers (9) live in the grid.

Transformation:
  * Every 9 that belongs to the *interior* of the maze (the region the box can
    reach, plus markers pressed against that region) is wiped to the local
    background color.  Markers that float in the open field outside the maze
    are kept.
  * The 3-box is then "charged": its 3/2 cells are overwritten with 9, one cell
    per wiped marker, filled in reading order (row-major).

`infer_T` builds the latent mask (which cells change and to what); `apply_T`
copies the input and overwrites only the masked cells.
"""


def _dims(g):
    return len(g), len(g[0])


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_single(grid, color):
    H, W = _dims(grid)
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color:
                return (r, c)
    return None


def _box_bounds(grid, border_color, center_color):
    """Bounding box of the small box = cells of border_color/center_color."""
    H, W = _dims(grid)
    cells = [(r, c) for r in range(H) for c in range(W)
             if grid[r][c] in (border_color, center_color)]
    if not cells:
        return None
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _flood(grid, starts, blocked, conn8=False, border_wall=False):
    """4/8-connected flood from `starts` avoiding cells whose value is in
    `blocked`; optionally treat the outermost ring of the grid as a wall."""
    H, W = _dims(grid)
    seen = set()
    stack = list(starts)
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if conn8:
        dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    while stack:
        r, c = stack.pop()
        if (r, c) in seen:
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if grid[r][c] in blocked:
            continue
        if border_wall and min(r, c, H - 1 - r, W - 1 - c) < 1:
            continue
        seen.add((r, c))
        for dr, dc in dirs:
            stack.append((r + dr, c + dc))
    return seen


def infer_T(input_grid):
    H, W = _dims(input_grid)
    grid = input_grid

    bg = _background(grid)

    # Identify the special colors: the box is the only colour appearing as a
    # tight 3x3 cluster with a unique centre marker.  We detect the marker
    # colour (appears exactly once inside the box) and the border colour.
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1

    # The wall/maze colour is the most frequent non-background structural colour.
    # Markers are the colour that gets collected; we discover them structurally.
    # Empirically: 6 = wall, 3 = box border, 2 = box centre, 9 = markers, 7 = bg.
    # Derive them generically instead of hardcoding values:
    #   centre = the colour with the smallest count (the single marker '2').
    centre_color = min(counts, key=counts.get)
    centre = _find_single(grid, centre_color)

    # box border = the colour forming the ring immediately around the centre.
    box_border = None
    if centre is not None:
        cr, cc = centre
        ring = {}
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = cr + dr, cc + dc
                if 0 <= r < H and 0 <= c < W:
                    ring[grid[r][c]] = ring.get(grid[r][c], 0) + 1
        if ring:
            box_border = max(ring, key=ring.get)

    # marker colour = the remaining frequent colour that is neither bg, wall,
    # border nor centre; equivalently the colour appearing both inside the box
    # bounds region edges and scattered.  We pick the colour (other than bg,
    # centre, box_border) that has the most isolated occurrences.
    wall_color = None
    marker_color = None
    bb = _box_bounds(grid, box_border, centre_color) if box_border is not None else None

    # candidate structural colours excluding bg/centre/border
    others = [col for col in counts
              if col not in (bg, centre_color, box_border)]
    # wall colour: the one most adjacent to the box border ring extension /
    # most frequent overall among others.
    if others:
        wall_color = max(others, key=lambda col: counts[col])
    marker_candidates = [col for col in others if col != wall_color]
    if marker_candidates:
        marker_color = max(marker_candidates, key=lambda col: counts[col])
    else:
        marker_color = None

    T = {}
    if centre is None or marker_color is None or bb is None:
        return T

    r0, c0, r1, c1 = bb

    # --- determine which markers are "collected" (wiped) ---
    nine = set((r, c) for r in range(H) for c in range(W)
               if grid[r][c] == marker_color)

    # leaky reach: flood from centre, only walls block
    leaky = _flood(grid, [centre], blocked={wall_color}, conn8=False)
    six = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == wall_color]
    if six:
        wr0 = min(r for r, c in six)
        wr1 = max(r for r, c in six)
        wc0 = min(c for r, c in six)
        wc1 = max(c for r, c in six)
    else:
        wr0, wc0, wr1, wc1 = 0, 0, H - 1, W - 1

    # interior region: flood from centre treating walls, markers and the grid
    # border as obstacles (markers seal off external fields).
    interior = _flood(grid, [centre], blocked={wall_color, marker_color},
                      conn8=False, border_wall=True)

    collected = set()
    for (r, c) in nine:
        # (a) reachable through the maze and lying within the wall bounding box
        if (r, c) in leaky and wr0 <= r <= wr1 and wc0 <= c <= wc1:
            collected.add((r, c))
            continue
        # (b) pressed against the interior region (8-adjacency)
        if any((r + dr, c + dc) in interior
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            collected.add((r, c))
            continue
        # (c) a straight ray (8 directions, blocked by walls) reaches interior
        hit = False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < H and 0 <= cc < W:
                if grid[rr][cc] == wall_color:
                    break
                if (rr, cc) in interior:
                    hit = True
                    break
                rr += dr
                cc += dc
            if hit:
                break
        if hit:
            collected.add((r, c))

    n = len(collected)

    # --- build the mask ---
    # wipe collected markers to background
    for (r, c) in collected:
        T[(r, c)] = bg

    # charge the box: overwrite n of its 3/2 cells with the marker colour in
    # reading order (row-major).
    box_cells = sorted((r, c) for r in range(H) for c in range(W)
                       if grid[r][c] in (box_border, centre_color))
    for (r, c) in box_cells[:n]:
        T[(r, c)] = marker_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
