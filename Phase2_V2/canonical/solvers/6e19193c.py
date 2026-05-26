def _components(grid):
    """Return list of (color, cells) for 8-connected non-zero components."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and (r, c) not in seen:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != col:
                        continue
                    seen.add((x, y))
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((x + dx, y + dy))
                comps.append((col, cells))
    return comps


def infer_T(input_grid):
    """Latent mask: each L-triomino's corner emits a diagonal ray.

    Each object is an L-shaped triomino with one 'corner' cell that has two
    orthogonal neighbours (the two arms). A diagonal ray, in the direction
    given by the sum of the two arm offsets, shoots out from the corner
    starting two cells beyond it, painting the object's colour to the edge.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for col, cells in _components(input_grid):
        s = set(cells)
        corner = None
        arms = None
        for (x, y) in cells:
            nb = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if (x + dx, y + dy) in s]
            if len(nb) == 2:
                corner = (x, y)
                arms = nb
        if corner is None:
            continue
        cx, cy = corner
        dr = sum(a[0] for a in arms)
        dc = sum(a[1] for a in arms)
        r, c = cx + 2 * dr, cy + 2 * dc
        while 0 <= r < H and 0 <= c < W:
            T[(r, c)] = col
            r += dr
            c += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
