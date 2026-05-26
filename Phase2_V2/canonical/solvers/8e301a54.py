"""Canonical solver for ARC puzzle 8e301a54.

Rule: the grid contains several solid-color objects on a background.
Each object falls straight DOWN by a number of rows equal to its own
cell count (size). Cells that fall off the bottom edge disappear.
The latent transformation mask T records, per affected cell, the new
color (background for vacated cells, object color for landed cells).
"""


def _objects(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or grid[y][x] != color:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((y + dy, x + dx))
                objs.append((color, cells))
    return objs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    objs = _objects(input_grid, bg)

    T = {}
    # First vacate every original object cell (set to background).
    for color, cells in objs:
        for (y, x) in cells:
            T[(y, x)] = bg
    # Then draw each object shifted down by its own size; later draws win.
    for color, cells in objs:
        shift = len(cells)
        for (y, x) in cells:
            ny = y + shift
            if 0 <= ny < H:
                T[(ny, x)] = color
    return T, bg


def apply_T(input_grid, T):
    mask, bg = T
    out = [row[:] for row in input_grid]
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
