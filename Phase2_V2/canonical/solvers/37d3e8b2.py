def _components(grid, color):
    """4/8-connected components of `color`; here used for the 8-colored shapes (8-connected)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1))
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or grid[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in dirs:
                        stack.append((rr + dr, cc + dc))
                comps.append(cells)
    return comps


def _hole_regions(grid, cells):
    """Count 4-connected background (0) regions strictly inside the bbox of `cells`."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    sub = [[grid[r0 + i][c0 + j] for j in range(w)] for i in range(h)]
    seen = [[False] * w for _ in range(h)]
    n = 0
    for i in range(h):
        for j in range(w):
            if sub[i][j] == 0 and not seen[i][j]:
                stack = [(i, j)]
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < h and 0 <= b < w):
                        continue
                    if seen[a][b] or sub[a][b] != 0:
                        continue
                    seen[a][b] = True
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                n += 1
    return n


def infer_T(input_grid):
    """Latent transformation mask: each 8-shape is recolored by its number of
    interior hole regions (1->1, 2->2, 3->3, 4->7)."""
    H, W = len(input_grid), len(input_grid[0])
    hole_to_color = {1: 1, 2: 2, 3: 3, 4: 7}
    T = [[None] * W for _ in range(H)]
    for cells in _components(input_grid, 8):
        nh = _hole_regions(input_grid, cells)
        color = hole_to_color.get(nh)
        if color is None:
            continue
        for r, c in cells:
            T[r][c] = color
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
