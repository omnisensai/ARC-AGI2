"""Canonical solver for ARC puzzle 8fbca751.

Rule
----
The grid contains separate shapes drawn in color 8 on a background of 0.
Shapes that are AXIS-ALIGNED with one another (their row-ranges overlap, or
their column-ranges overlap) belong to the same "region"; shapes that are only
diagonally related stay in distinct regions.  For each region the axis-aligned
bounding box that covers all its shapes is computed, and every background (0)
cell inside that bounding box is repainted with 2.  Cells that already hold an
8 are left untouched, as is everything outside the regions.

The latent transformation T is the mask of cells that change to 2.
"""


def _components(grid):
    """4-connected components of color-8 cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 8 and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in seen:
                        continue
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if grid[cr][cc] != 8:
                        continue
                    seen.add((cr, cc))
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(comp)
    return comps


def _bbox(comp):
    rs = [p[0] for p in comp]
    cs = [p[1] for p in comp]
    return [min(rs), max(rs), min(cs), max(cs)]


def _ranges_overlap(a0, a1, b0, b1):
    return not (a1 < b0 or b1 < a0)


def _aligned(a, b):
    """Two bounding boxes belong together if they are axis-aligned:
    their row-ranges overlap, or their column-ranges overlap.
    Purely diagonal boxes (neither overlap) stay separate."""
    return (_ranges_overlap(a[0], a[1], b[0], b[1]) or
            _ranges_overlap(a[2], a[3], b[2], b[3]))


def _regions(grid):
    """Group shape bounding boxes into aligned regions, returning the
    merged bounding box (r0, r1, c0, c1) of each region."""
    boxes = [_bbox(c) for c in _components(grid)]
    n = len(boxes)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _aligned(boxes[i], boxes[j]):
                parent[find(i)] = find(j)

    grouped = {}
    for i in range(n):
        grouped.setdefault(find(i), []).append(boxes[i])

    regions = []
    for gb in grouped.values():
        regions.append((
            min(b[0] for b in gb),
            max(b[1] for b in gb),
            min(b[2] for b in gb),
            max(b[3] for b in gb),
        ))
    return regions


def infer_T(input_grid):
    """Latent mask: cells (background 0) inside each region's bounding box
    that should be repainted to 2."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for r0, r1, c0, c1 in _regions(input_grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if input_grid[r][c] == 0:
                    T[r][c] = 2
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
