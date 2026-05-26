from collections import deque


def _components(grid):
    """8-connected single-color connected components (non-zero)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y < 0 or y >= H or x < 0 or x >= W or
                            seen[y][x] or grid[y][x] != col):
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((y + dy, x + dx))
                comps.append((col, cells))
    return comps


def infer_T(input_grid):
    """Latent mask: {(r,c): frame_color}.

    A legend lives in columns 0-1 of the left edge: each row with both cols
    non-zero maps shape_color (col0) -> frame_color (col1). Every scattered
    shape elsewhere in the grid gets a 1-cell-thick frame around its bounding
    box. The frame color floods the background of the (clamped) expanded
    bounding box from its border inward, so background pockets enclosed by the
    shape stay untouched.
    """
    grid = input_grid
    H, W = len(grid), len(grid[0])

    legend = {}
    for r in range(H):
        if grid[r][0] != 0 and grid[r][1] != 0:
            legend[grid[r][0]] = grid[r][1]

    T = {}
    for col, cells in _components(grid):
        if col not in legend:
            continue
        cs = [x for _, x in cells]
        if max(cs) < 2:          # the legend strip itself (cols 0-1) -> skip
            continue
        rs = [y for y, _ in cells]
        fc = legend[col]
        r0, r1 = max(0, min(rs) - 1), min(H - 1, max(rs) + 1)
        c0, c1 = max(0, min(cs) - 1), min(W - 1, max(cs) + 1)

        fill = set()
        q = deque()
        for c in range(c0, c1 + 1):
            for rr in (r0, r1):
                if grid[rr][c] == 0:
                    q.append((rr, c))
        for r in range(r0, r1 + 1):
            for cc in (c0, c1):
                if grid[r][cc] == 0:
                    q.append((r, cc))
        while q:
            y, x = q.popleft()
            if ((y, x) in fill or not (r0 <= y <= r1 and c0 <= x <= c1)
                    or grid[y][x] != 0):
                continue
            fill.add((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q.append((y + dy, x + dx))

        for cell in fill:
            T[cell] = fc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
