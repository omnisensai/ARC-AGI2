def infer_T(input_grid):
    """Latent mask: for every non-background connected object, clear the two
    leftmost columns of its bounding box (overwrite them with background).
    Objects of width <= 2 are removed entirely."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and not seen[r][c]:
                col = input_grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or input_grid[y][x] != col:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                cmin = min(x for _, x in cells)
                for (y, x) in cells:
                    if x < cmin + 2:
                        T[(y, x)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
