"""Canonical latent-T solver for ARC puzzle d931c21c.

Rule: the grid contains hollow outline shapes drawn with color 1 on a 0
background. Treat each 8-connected component of 1s as a shape. A shape that
fully ENCLOSES an interior region (background cells unreachable from the grid
border) is "closed" and gets decorated:
  - every interior background cell 8-adjacent to one of the shape's 1s -> 3
  - every exterior background cell 8-adjacent to one of the shape's 1s -> 2
Shapes whose outline is broken (no enclosed interior) are left untouched.
"""

NEIGHBORS8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
NEIGHBORS4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _outside_region(grid):
    """Background (0) cells reachable from the grid border via 4-connectivity."""
    H, W = len(grid), len(grid[0])
    outside = set()
    stack = [(r, c) for r in range(H) for c in range(W)
             if (r == 0 or c == 0 or r == H - 1 or c == W - 1) and grid[r][c] == 0]
    while stack:
        r, c = stack.pop()
        if (r, c) in outside or not (0 <= r < H and 0 <= c < W):
            continue
        if grid[r][c] != 0:
            continue
        outside.add((r, c))
        for dr, dc in NEIGHBORS4:
            stack.append((r + dr, c + dc))
    return outside


def _components(grid):
    """8-connected components of color-1 cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 1 and (r, c) not in seen:
                comp = set()
                stack = [(r, c)]
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != 1:
                        continue
                    seen.add((a, b))
                    comp.add((a, b))
                    for dr, dc in NEIGHBORS8:
                        stack.append((a + dr, b + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    outside = _outside_region(input_grid)
    interior = set((r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] == 0 and (r, c) not in outside)

    T = {}
    for comp in _components(input_grid):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # Closed iff it encloses at least one interior background cell.
        encloses = any((r, c) in interior
                       for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
        if not encloses:
            continue
        for r, c in comp:
            for dr, dc in NEIGHBORS8:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    continue
                if (nr, nc) in interior:
                    T[(nr, nc)] = 3
                elif (nr, nc) in outside:
                    T[(nr, nc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
