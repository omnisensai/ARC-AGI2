"""Canonical latent-T solver for ARC puzzle dd6b8c4b.

Each input contains:
  * a background colour that fills empty space,
  * a wall colour that draws a maze of rooms/rings,
  * a small 3x3 box (a border colour around a single unique centre marker),
  * scattered single-cell marker dots of one colour.

Rule:
  * Markers that lie in the *interior* of the maze (reachable from the box,
    or pressed against / aimed at that interior) are wiped to the background.
  * The 3x3 box is then "charged": its border/centre cells are overwritten
    with the marker colour, one cell per wiped marker, in row-major order.

`infer_T` derives the colour roles from the input structure and builds the
latent mask of changed cells; `apply_T` copies the input and overwrites only
those cells.
"""


def _dims(g):
    return len(g), len(g[0])


def _color_counts(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return counts


def _detect_roles(grid):
    """Return (bg, wall, box_border, centre_color, centre, marker)."""
    H, W = _dims(grid)
    counts = _color_counts(grid)

    centre_color = None
    centre = None
    box_border = None
    for color in sorted(counts, key=counts.get):
        cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == color]
        if len(cells) != 1:
            continue
        r, c = cells[0]
        ring = {}
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < H and 0 <= cc < W:
                    ring[grid[rr][cc]] = ring.get(grid[rr][cc], 0) + 1
        if ring and max(ring.values()) >= 6:
            centre_color = color
            centre = (r, c)
            box_border = max(ring, key=ring.get)
            break
    if centre is None:
        return None

    others = [col for col in counts if col not in (centre_color, box_border)]

    def largest_component(color):
        seen = set()
        best = 0
        for r in range(H):
            for c in range(W):
                if grid[r][c] != color or (r, c) in seen:
                    continue
                stack = [(r, c)]
                size = 0
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W) or grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    size += 1
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                best = max(best, size)
        return best

    wall_color = None
    if others:
        wall_color = max(others, key=lambda col: (largest_component(col), counts[col]))

    rest = [col for col in others if col != wall_color]
    bg = max(rest, key=lambda col: counts[col]) if rest else 0
    marker_candidates = [col for col in rest if col != bg]
    marker_color = max(marker_candidates, key=lambda col: counts[col]) \
        if marker_candidates else None

    return bg, wall_color, box_border, centre_color, centre, marker_color


def _flood(grid, start, wall_set, border_wall=False):
    H, W = _dims(grid)
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) in seen:
                continue
            if grid[nr][nc] in wall_set:
                continue
            if border_wall and min(nr, nc, H - 1 - nr, W - 1 - nc) < 1:
                continue
            seen.add((nr, nc))
            stack.append((nr, nc))
    return seen


def infer_T(input_grid):
    grid = input_grid
    H, W = _dims(grid)
    T = {}

    roles = _detect_roles(grid)
    if roles is None:
        return T
    bg, wall, border, centre_color, centre, marker = roles
    if centre is None or marker is None:
        return T

    markers = set((r, c) for r in range(H) for c in range(W)
                  if grid[r][c] == marker)

    leaky = _flood(grid, centre, {wall})

    walls = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == wall]
    if walls:
        wr0 = min(r for r, c in walls)
        wr1 = max(r for r, c in walls)
        wc0 = min(c for r, c in walls)
        wc1 = max(c for r, c in walls)
    else:
        wr0, wc0, wr1, wc1 = 0, 0, H - 1, W - 1

    interior = _flood(grid, centre, {wall, marker}, border_wall=True)

    collected = set()
    for (r, c) in markers:
        if (r, c) in leaky and wr0 <= r <= wr1 and wc0 <= c <= wc1:
            collected.add((r, c))
            continue
        if any((r + dr, c + dc) in interior
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            collected.add((r, c))
            continue
        hit = False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < H and 0 <= cc < W:
                if grid[rr][cc] == wall:
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

    for (r, c) in collected:
        T[(r, c)] = bg

    box_cells = sorted((r, c) for r in range(H) for c in range(W)
                       if grid[r][c] in (border, centre_color))
    for (r, c) in box_cells[:n]:
        T[(r, c)] = marker

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
