"""Canonical solver for ARC puzzle e619ca6e.

Rule: every solid rectangle of color 3 is a "seed". Each seed spawns two
diagonal chains of copies of itself. The left chain repeatedly shifts the
rectangle down by its own height and left by its own width; the right chain
shifts down by its height and right by its width. Chains continue until they
fall off the grid (clipped at the borders). All produced cells are painted 3.
"""


def _components(grid, color):
    """Find axis-aligned rectangle components of `color` (4-connected)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    rects = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if seen[cr][cc] or grid[cr][cc] != color:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                rs = [x[0] for x in cells]
                cs = [x[1] for x in cells]
                rects.append((min(rs), min(cs), max(rs), max(cs)))
    return rects


def infer_T(input_grid):
    """Return latent mask dict {(r,c): 3} of all cells to paint."""
    H, W = len(input_grid), len(input_grid[0])
    color = 3
    mask = {}

    def paint(r0, r1, a, b):
        for r in range(r0, r1 + 1):
            for c in range(a, b + 1):
                if 0 <= r < H and 0 <= c < W:
                    mask[(r, c)] = color

    for (r0, c0, r1, c1) in _components(input_grid, color):
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        # original seed
        paint(r0, r1, c0, c1)
        # left chain: down by h, left by w each step
        rr, a, b = r0, c0, c1
        while True:
            rr += h
            a -= w
            b -= w
            if rr > H - 1 or b < 0:
                break
            paint(rr, rr + h - 1, max(a, 0), b)
        # right chain: down by h, right by w each step
        rr, a, b = r0, c0, c1
        while True:
            rr += h
            a += w
            b += w
            if rr > H - 1 or a > W - 1:
                break
            paint(rr, rr + h - 1, a, min(b, W - 1))

    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
