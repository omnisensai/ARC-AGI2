def _components(grid):
    """Connected (4-neighbour, same-color) non-zero components, in scan order
    (top-to-bottom, left-to-right by first-touched cell)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W):
                        continue
                    if seen[a][b] or grid[a][b] != color:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Latent mask: the grid is a vertical stack of non-zero shapes. Reading the
    shapes in scan order, every 3rd shape (index % 3 == 0) is recolored to 2."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for i, cells in enumerate(_components(input_grid)):
        if i % 3 == 0:
            for r, c in cells:
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
