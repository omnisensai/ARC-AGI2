"""Canonical solver for ARC puzzle 15663ba9.

Rule: the input contains 1-cell-wide closed loops drawn in a single non-zero
color. Each loop encloses an interior region. At every cell where the loop
turns a corner (it has exactly one vertical loop-neighbor and one horizontal
loop-neighbor):
  - if the loop's enclosed interior fills the diagonal cell "inside the bend"
    (a convex / outward-pointing corner) the corner cell is recolored 4;
  - otherwise (a concave / inward-pointing corner) the corner cell is recolored 2.
Straight segments and background are left unchanged.
"""


def _components(grid):
    """8-connected connected components of non-zero cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W) or seen[a][b] or grid[a][b] == 0:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def _interior(cells):
    """Cells enclosed by a loop: background cells (4-connectivity) that cannot
    reach the loop's padded bounding-box border without crossing the loop."""
    cellset = set(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs) - 1, max(rs) + 1
    c0, c1 = min(cs) - 1, max(cs) + 1
    outside = set()
    stack = []
    for r in range(r0, r1 + 1):
        for c in (c0, c1):
            if (r, c) not in cellset:
                stack.append((r, c))
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            if (r, c) not in cellset:
                stack.append((r, c))
    while stack:
        a, b = stack.pop()
        if not (r0 <= a <= r1 and c0 <= b <= c1) or (a, b) in outside or (a, b) in cellset:
            continue
        outside.add((a, b))
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            stack.append((a + dr, b + dc))
    inside = set()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) not in cellset and (r, c) not in outside:
                inside.add((r, c))
    return inside


def infer_T(input_grid):
    """Latent mask: {(r, c): new_color} of corner cells to recolor (4 or 2)."""
    H, W = len(input_grid), len(input_grid[0])
    inside_all = set()
    for cells in _components(input_grid):
        inside_all |= _interior(cells)
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                continue
            vert = [(dr, dc) for dr, dc in ((-1, 0), (1, 0))
                    if 0 <= r + dr < H and 0 <= c + dc < W and input_grid[r + dr][c + dc] != 0]
            horiz = [(dr, dc) for dr, dc in ((0, -1), (0, 1))
                     if 0 <= r + dr < H and 0 <= c + dc < W and input_grid[r + dr][c + dc] != 0]
            if len(vert) == 1 and len(horiz) == 1:
                vdr = vert[0][0]
                hdc = horiz[0][1]
                bend_diag = (r + vdr, c + hdc)  # cell tucked into the corner
                T[(r, c)] = 4 if bend_diag in inside_all else 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
