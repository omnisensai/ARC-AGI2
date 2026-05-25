"""Canonical solver for ARC puzzle 320afe60.

Rule (single transformation):
  The background is the most common color (4). The grid contains several blue (1)
  connected objects scattered around. Each object is recolored and slid
  horizontally to one of the two side edges, preserving its exact shape and its
  row span:

    - CLOSED objects  -> recolored 2, slid to the LEFT  edge (leftmost cell -> col 0)
    - OPEN cup objects -> recolored 3, slid to the RIGHT edge (rightmost cell -> col W-1)

  "Closed" means the object is either solid or hollow with a fully-enclosed
  interior cavity (a hole completely surrounded by the object). "Open" (a cup /
  C-shape) means the object is hollow and its interior connects to the outside
  through a gap in its perimeter.

  The original blue cells are cleared to background; only the relocated,
  recolored copies remain.

Canonical latent-T form: infer_T builds a {(r,c): new_color} mask plus the set
of original object cells to clear; apply_T copies the input, clears the original
object cells, then paints the mask.
"""

from collections import deque


def _connected_objects(grid, color, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    a, b = stack.pop()
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + dr, b + dc
                        if 0 <= na < H and 0 <= nb < W and grid[na][nb] == color and not seen[na][nb]:
                            seen[na][nb] = True
                            stack.append((na, nb))
                objs.append(cells)
    return objs


def _is_closed(cells):
    """True if the object is solid or has a fully-enclosed interior cavity."""
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    local = set((a - r0, b - c0) for (a, b) in cells)
    if len(cells) == h * w:
        return True  # solid rectangle -> closed
    # Flood-fill the empties from a 1-cell padded border. Any empty cell within
    # the bounding box that is NOT reached is a fully-enclosed cavity.
    H2, W2 = h + 2, w + 2
    filled = [[False] * W2 for _ in range(H2)]
    for (a, b) in local:
        filled[a + 1][b + 1] = True
    reached = [[False] * W2 for _ in range(H2)]
    dq = deque([(0, 0)])
    reached[0][0] = True
    while dq:
        a, b = dq.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            na, nb = a + dr, b + dc
            if 0 <= na < H2 and 0 <= nb < W2 and not reached[na][nb] and not filled[na][nb]:
                reached[na][nb] = True
                dq.append((na, nb))
    for a in range(H2):
        for b in range(W2):
            if not filled[a][b] and not reached[a][b]:
                return True  # enclosed cavity present -> closed
    return False  # open cup


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # object color = most common non-background color (the shapes), here blue/1
    fg_counts = {k: v for k, v in counts.items() if k != bg}
    if not fg_counts:
        return ({}, set())
    obj_color = max(fg_counts, key=fg_counts.get)

    clear = set()
    paint = {}  # (r, c) -> new color
    for cells in _connected_objects(input_grid, obj_color, bg):
        clear.update(cells)
        cs = [c[1] for c in cells]
        c0, c1 = min(cs), max(cs)
        if _is_closed(cells):
            new_color = 2
            shift = -c0          # slide so leftmost cell -> col 0
        else:
            new_color = 3
            shift = (W - 1) - c1  # slide so rightmost cell -> col W-1
        for (r, c) in cells:
            paint[(r, c + shift)] = new_color
    return (paint, clear)


def apply_T(input_grid, T):
    paint, clear = T
    out = [row[:] for row in input_grid]
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    for (r, c) in clear:
        out[r][c] = bg
    for (r, c), v in paint.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
