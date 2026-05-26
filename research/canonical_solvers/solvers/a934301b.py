def _components(grid):
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
                    if a < 0 or a >= H or b < 0 or b >= W:
                        continue
                    if seen[a][b] or grid[a][b] == 0:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    # T is a latent mask of cells to clear (set to background 0).
    # Rule: each non-zero object is a rectangular block of 1s containing
    # some 8 markers. An object survives if it has at most one 8 marker;
    # objects with two or more 8s are erased.
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for cells in _components(input_grid):
        n8 = sum(1 for (a, b) in cells if input_grid[a][b] == 8)
        if n8 >= 2:
            for (a, b) in cells:
                T[a][b] = 0
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
