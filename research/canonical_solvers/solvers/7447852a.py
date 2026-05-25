def _components(grid, bg):
    """Flood-fill (4-connectivity) the background-colored cells into regions."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    regions = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg and not seen[r][c]:
                stack = [(r, c)]
                comp = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or grid[y][x] != bg:
                        continue
                    seen[y][x] = True
                    comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                regions.append(comp)
    return regions


def infer_T(input_grid):
    """Compute the latent fill mask.

    The 2s trace a zig-zag of diamonds; the empty interiors form two bands of
    diamond regions: a 'top' band touching the first row and a 'bottom' band
    touching the last row.  Ordering each band left-to-right, we fill (color 4)
    the top regions whose index is congruent to 1 mod 3 and the bottom regions
    whose index is congruent to 0 mod 3.
    """
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    regions = _components(input_grid, bg)
    top = [reg for reg in regions if any(y == 0 for y, x in reg)]
    bot = [reg for reg in regions if any(y == H - 1 for y, x in reg)]
    top.sort(key=lambda reg: min(x for y, x in reg))
    bot.sort(key=lambda reg: min(x for y, x in reg))

    T = [[None] * W for _ in range(H)]
    for i, reg in enumerate(top):
        if i % 3 == 1:
            for y, x in reg:
                T[y][x] = 4
    for i, reg in enumerate(bot):
        if i % 3 == 0:
            for y, x in reg:
                T[y][x] = 4
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
