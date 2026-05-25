"""Canonical latent-T solver for ARC puzzle 3d588dc9.

Rule (single transformation, same-size):
  Every grid contains several "block" objects of color 0 that are a solid
  3x4 / 4x3 rectangle (12 cells) plus a 2-cell protruding "tail" (14 cells
  total).  One color-5 right-triangle "staircase" acts as the legend: it sits
  in the same horizontal band (row overlap) as exactly ONE of those blocks and
  points at it from one horizontal side.

  For that pointed-at block:
    * the protruding tail is erased (set to background 7), and
    * the block's vertical edge that FACES the legend staircase (the column of
      the rectangle nearest the staircase) is recolored with 6.

  All other objects (the distractor staircases, single-cell markers, and the
  un-pointed blocks) are left untouched.

`infer_T` builds an explicit {(r,c): new_color} mask from the input alone;
`apply_T` copies the input and overwrites only the masked cells.
"""

BG = 7
LEGEND_COLOR = 5      # the indicator staircase color for this task family
MARK = 6
BLOCK_COLOR = 0
BLOCK_SIZE = 14


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen:
                        continue
                    if not (0 <= a < H and 0 <= b < W) or grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _staircase_corner(cells):
    """Return the right-angle corner ('TL'/'TR'/'BL'/'BR') of a staircase
    right-triangle, or None if the shape is not such a triangle."""
    s = set(cells)
    r0, r1, c0, c1 = _bbox(cells)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    if h < 3 or w < 3:
        return None
    if len(cells) >= h * w * 0.9:        # essentially a full rectangle
        return None
    top = all((r0, c) in s for c in range(c0, c1 + 1))
    bot = all((r1, c) in s for c in range(c0, c1 + 1))
    left = all((r, c0) in s for r in range(r0, r1 + 1))
    right = all((r, c1) in s for r in range(r0, r1 + 1))
    if top and left:
        return 'TL'
    if top and right:
        return 'TR'
    if bot and left:
        return 'BL'
    if bot and right:
        return 'BR'
    return None


def _largest_rectangle(cells):
    """Largest solid axis-aligned rectangle fully covered by `cells`
    (the rectangular body of a block, excluding its tail)."""
    s = set(cells)
    r0, r1, c0, c1 = _bbox(cells)
    best = None
    best_area = 0
    for a in range(r0, r1 + 1):
        for b in range(a, r1 + 1):
            for k0 in range(c0, c1 + 1):
                for k1 in range(k0, c1 + 1):
                    if all((rr, kk) in s
                           for rr in range(a, b + 1)
                           for kk in range(k0, k1 + 1)):
                        area = (b - a + 1) * (k1 - k0 + 1)
                        if area > best_area:
                            best_area = area
                            best = (a, b, k0, k1)
    return best


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    T = {}

    # 1. Locate the legend staircase (color 5, right-triangle shape).
    legend = None
    for cells in _components(input_grid, LEGEND_COLOR):
        if _staircase_corner(cells) is not None:
            legend = _bbox(cells)
            break
    if legend is None:
        return T
    lr0, lr1, lc0, lc1 = legend

    # 2. Among the size-14 color-0 blocks, pick the one sharing the legend's
    #    horizontal band (row overlap > 0).
    target = None
    for cells in _components(input_grid, BLOCK_COLOR):
        if len(cells) != BLOCK_SIZE:
            continue
        r0, r1, _, _ = _bbox(cells)
        if max(0, min(r1, lr1) - max(r0, lr0) + 1) > 0:
            target = cells
            break
    if target is None:
        return T

    # 3. Split the block into its rectangular body and its tail.
    rect = _largest_rectangle(target)
    a, b, k0, k1 = rect
    body = set((r, c) for r in range(a, b + 1) for c in range(k0, k1 + 1))

    # 4. Erase the tail.
    for (r, c) in target:
        if (r, c) not in body:
            T[(r, c)] = BG

    # 5. Recolor the body's vertical edge that faces the legend staircase
    #    (the rectangle column nearest the legend), with color 6.
    block_center_c = (k0 + k1) / 2.0
    legend_center_c = (lc0 + lc1) / 2.0
    edge_col = k1 if legend_center_c > block_center_c else k0
    for r in range(a, b + 1):
        T[(r, edge_col)] = MARK

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
