def _components(g):
    """Connected components (4-connectivity) of color-2 cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 2 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W) or seen[a][b] or g[a][b] != 2:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Border markers (color 1) define full-grid lines. A vertical line is
    drawn at the column of a top/bottom marker; a horizontal line at the row
    of a left/right marker. Every line cell becomes 1; any color-2 block the
    line passes through is fully recolored to 1."""
    H, W = len(input_grid), len(input_grid[0])

    vcols, hrows = set(), set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                if r in (0, H - 1):
                    vcols.add(c)
                if c in (0, W - 1):
                    hrows.add(r)

    T = {}
    # Draw the lines across the full grid.
    for c in vcols:
        for r in range(H):
            T[(r, c)] = 1
    for r in hrows:
        for c in range(W):
            T[(r, c)] = 1

    # Recolor any block that a line passes through.
    for cells in _components(input_grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        rmin, rmax = min(rs), max(rs)
        cmin, cmax = min(cs), max(cs)
        crossed = any(cmin <= vc <= cmax for vc in vcols) or \
                  any(rmin <= hr <= rmax for hr in hrows)
        if crossed:
            for (r, c) in cells:
                T[(r, c)] = 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
