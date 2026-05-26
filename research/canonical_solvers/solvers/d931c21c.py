"""Canonical latent-T solver for ARC puzzle d931c21c.

Rule
----
The grid shows hollow outline shapes drawn in color 1 on a 0 background. Treat
each 8-connected component of 1s as a shape. A shape is "closed" iff it fully
ENCLOSES an interior region (background cells unreachable from the grid border).
Closed shapes are decorated; shapes with a broken outline are left untouched.

For every closed shape (with outline cells `S` and the cells `I` it encloses):
  - interior fill: each enclosed background cell 8-adjacent to an outline cell
    becomes 3 (deeper interior cells, touching no outline, stay 0);
  - outer border: each exterior (border-reachable) background cell 8-adjacent to
    the shape's solid (outline + interior) becomes 2;
  - corner closure: the four bounding-box corners of the shape (offset outward by
    one cell) become 2 as well, but only when that corner is exterior and both of
    its flanking border cells already belong to the border ring. This rounds the
    convex outer corners while leaving concave / notched corners alone.

All of this is computed from the input alone; apply_T overwrites only the cells
named in the mask.
"""

NEIGHBORS8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
NEIGHBORS4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _outside_region(grid):
    """Background (0) cells reachable from the grid border (4-connectivity)."""
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

        # enclosed background cells of this shape
        enc = set((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if (r, c) in interior)
        if not enc:
            continue  # open outline -> untouched

        # interior fill (3) and outer border (2) via 8-adjacency to the OUTLINE.
        # (Cells touching only other interior cells, e.g. the very centre, stay 0.)
        border = set()
        for r, c in comp:
            for dr, dc in NEIGHBORS8:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    continue
                if (nr, nc) in enc:
                    T[(nr, nc)] = 3
                elif (nr, nc) in outside:
                    T[(nr, nc)] = 2
                    border.add((nr, nc))

        # close convex outer corners of the bounding box
        for cr, cc, ar, ac in (
            (r0 - 1, c0 - 1, r0 - 1, c0), (r0 - 1, c1 + 1, r0 - 1, c1),
            (r1 + 1, c0 - 1, r1 + 1, c0), (r1 + 1, c1 + 1, r1 + 1, c1),
        ):
            if not (0 <= cr < H and 0 <= cc < W) or (cr, cc) not in outside:
                continue
            arm_h = (cr, c0 if cc < c0 else c1)
            arm_v = (r0 if cr < r0 else r1, cc)
            if arm_h in border and arm_v in border:
                T[(cr, cc)] = 2

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
