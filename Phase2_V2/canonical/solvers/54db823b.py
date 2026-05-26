def infer_T(input_grid):
    """Latent mask: erase the single object that contains the fewest 9-cells.

    The grid holds several rectangular blocks (drawn in colors 3 and 9) on a
    black (0) background. Exactly one block -- the one with the smallest count
    of 9 cells -- is removed; every other block is left untouched. T maps each
    cell of the chosen block to 0.
    """
    H, W = len(input_grid), len(input_grid[0])

    # connected components of non-background cells (8-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W):
                        continue
                    if seen[y][x] or input_grid[y][x] == 0:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((y + dy, x + dx))
                comps.append(cells)

    T = {}
    if not comps:
        return T

    def count9(cells):
        return sum(1 for (y, x) in cells if input_grid[y][x] == 9)

    target = min(comps, key=count9)
    for (y, x) in target:
        T[(y, x)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
