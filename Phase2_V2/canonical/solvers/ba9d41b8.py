def _components(grid, color):
    """Connected components (4-neighbor) of `color` in grid."""
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] != color:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
                out.append(cells)
    return out


def infer_T(input_grid):
    """Latent mask: for each solid colored rectangle, carve a checkerboard
    into its interior (keep the 1-cell border). An interior cell at local
    offset (i', j') from the interior's top-left becomes background (0) when
    (i' + j') is even."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    colors = set(v for row in input_grid for v in row if v != 0)
    for color in colors:
        for cells in _components(input_grid, color):
            rs = [y for y, x in cells]
            xs = [x for y, x in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(xs), max(xs)
            # only treat as a filled rectangle if it actually is one
            if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
                continue
            for y in range(r0 + 1, r1):
                for x in range(c0 + 1, c1):
                    ip = y - (r0 + 1)
                    jp = x - (c0 + 1)
                    if (ip + jp) % 2 == 0:
                        T[y][x] = 0
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
