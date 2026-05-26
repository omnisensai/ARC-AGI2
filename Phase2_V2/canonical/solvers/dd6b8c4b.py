"""Canonical latent-T solver for ARC task dd6b8c4b.

Structure of the task (all color roles inferred from input structure, no literals):
  - background (bg): the color that fills the grid frame/border.
  - a 3x3 "charge box": a unique single-cell CENTER marker surrounded by a uniform
    8-neighborhood ring of a BORDER color (the box border).
  - MARKER color: scattered single/small components floating in the field.
  - WALL color (if any): the remaining structural color forming a maze of corridors.

Transform:
  - Flood from the cells immediately around the charge box, travelling through
    background + marker cells, blocked by walls and by the box border. Markers the
    flood reaches are "drawn into" the box. The box has 9 cells, so at most 9 markers
    can be charged: keep only the 9 nearest (by corridor geodesic distance).
  - Those reached markers are wiped to background.
  - The box's 9 cells (border + center) are filled with the marker color in
    row-major order, one cell per wiped marker.
"""

from collections import deque, Counter


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                out.append(comp)
    return out


def _infer_roles(grid):
    """Derive (bg, center_color, box_border_color, marker_color) structurally."""
    H, W = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row)

    # background = most common color on the grid frame.
    border_cells = [grid[r][c] for r in range(H) for c in range(W)
                    if r in (0, H - 1) or c in (0, W - 1)]
    bg = Counter(border_cells).most_common(1)[0][0]

    # charge box: a single cell whose full 8-neighborhood is a uniform ring of one
    # other color (the box border). The single cell is the center marker.
    center_color = None
    box_border_color = None
    for color in counts:
        for comp in _components(grid, color):
            if len(comp) != 1:
                continue
            r, c = comp[0]
            ring = []
            ok = True
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < H and 0 <= cc < W):
                        ok = False
                        break
                    ring.append(grid[rr][cc])
                if not ok:
                    break
            if ok and len(set(ring)) == 1 and ring[0] != color:
                center_color = color
                box_border_color = ring[0]

    # marker = the remaining color that occurs in the most small (singleton/pair)
    # components — the scattered field markers.
    marker_color = None
    best = -1
    for color in counts:
        if color in (bg, center_color, box_border_color):
            continue
        small = sum(1 for comp in _components(grid, color) if len(comp) <= 2)
        if small > best:
            best = small
            marker_color = color

    return bg, center_color, box_border_color, marker_color


def infer_T(input_grid):
    """Return a latent transformation mask dict {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg, center_color, box_border_color, marker_color = _infer_roles(input_grid)

    T = {}
    if center_color is None or marker_color is None:
        return T

    # locate the charge box center.
    center = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == center_color:
                center = (r, c)
    if center is None:
        return T
    cr, cc = center
    box = set((cr + dr, cc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))

    def passable(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] in (bg, marker_color)

    # corridor geodesic flood starting from the free cells adjacent to the box,
    # travelling through background + markers (walls and the box border block it).
    dist = {}
    dq = deque()
    for r in range(H):
        for c in range(W):
            if (r, c) in box:
                continue
            if passable(r, c) and any((r + a, c + b) in box
                                      for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dist[(r, c)] = 0
                dq.append((r, c))
    while dq:
        r, c = dq.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if passable(nr, nc) and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                dq.append((nr, nc))

    # markers reachable from the box, sorted by corridor distance (row-major tie-break).
    reachable = [(r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == marker_color and (r, c) in dist]
    reachable.sort(key=lambda m: (dist[m], m[0], m[1]))

    # the box can hold at most len(box) charges (its 9 cells); take the nearest.
    capacity = len(box)
    drawn = reachable[:capacity]

    # wipe the drawn markers to background.
    for (r, c) in drawn:
        T[(r, c)] = bg

    # charge the box cells in row-major order, one per drawn marker.
    box_cells = sorted(box, key=lambda m: (m[0], m[1]))
    for k in range(len(drawn)):
        br, bcl = box_cells[k]
        T[(br, bcl)] = marker_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
