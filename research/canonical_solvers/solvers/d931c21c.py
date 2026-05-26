"""Canonical solver for ARC puzzle d931c21c.

Rule (single transformation):
  The grid contains hollow shapes drawn with color 1. Some shapes are "spirals":
  their wall winds around so that the inner corridor is sealed off from the
  outside under 4-connectivity (diagonal wall cells block 4-connected leakage,
  even though the wall itself is one 8-connected piece). A shape that seals such
  an interior gets decorated; an open shape (e.g. a plain box with a gap whose
  inside leaks to the border) is left untouched.

  For every spiral shape:
    - Background cells OUTSIDE (reachable from the grid border by 4-connectivity)
      that are 8-adjacent to the shape's wall are painted 2.
    - Background cells INSIDE (not reachable from the border by 4-connectivity)
      are painted 3 if they are 8-adjacent to any wall cell, otherwise they are
      left as 0 (the dead-end pocket at the spiral's core).

Canonical latent-T form: infer_T builds a {(r,c): new_color} mask from input
structure alone; apply_T copies the input and overwrites only masked cells.
"""


def _components(grid):
    """8-connected components of color-1 cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 1 and (r, c) not in seen:
                stack = [(r, c)]
                cells = set()
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != 1:
                        continue
                    seen.add((rr, cc))
                    cells.add((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append(cells)
    return comps


def _outside(grid):
    """Background cells reachable from the grid border by 4-connectivity."""
    H, W = len(grid), len(grid[0])
    out = set()
    stack = []
    for r in range(H):
        stack.append((r, 0))
        stack.append((r, W - 1))
    for c in range(W):
        stack.append((0, c))
        stack.append((H - 1, c))
    while stack:
        r, c = stack.pop()
        if not (0 <= r < H and 0 <= c < W) or (r, c) in out or grid[r][c] == 1:
            continue
        out.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    return out


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    outside = _outside(input_grid)
    T = {}

    def neighbors8(r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    yield r + dr, c + dc

    for cells in _components(input_grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # interior = background cells in bbox not reachable from outside
        interior = set()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if input_grid[r][c] != 1 and (r, c) not in outside:
                    interior.add((r, c))

        if not interior:
            # open shape: leave untouched
            continue

        # outside cells 8-adjacent to this wall -> 2
        for r, c in cells:
            for nr, nc in neighbors8(r, c):
                if 0 <= nr < H and 0 <= nc < W and (nr, nc) in outside:
                    T[(nr, nc)] = 2

        # interior cells -> 3 if 8-adjacent to a wall, else stay 0
        for r, c in interior:
            touches_wall = any(
                (nr, nc) in cells for nr, nc in neighbors8(r, c)
            )
            if touches_wall:
                T[(r, c)] = 3

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
