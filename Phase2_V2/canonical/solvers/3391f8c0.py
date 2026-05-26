from collections import deque


def _components(grid, color):
    """8-connected components of `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cells = []
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            a, b = x + dx, y + dy
                            if 0 <= a < H and 0 <= b < W and grid[a][b] == color and (a, b) not in seen:
                                seen.add((a, b))
                                q.append((a, b))
                comps.append(cells)
    return comps


def _norm(cells):
    """Cells relative to bounding-box top-left."""
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def infer_T(input_grid):
    """Build a latent mask {(r,c): new_color}.

    Two non-zero colors are present: one ("multi") appears as several identical
    shapes, the other ("single") appears once. Each multi-copy is overwritten
    with the single's shape (recolored to the single color), and the single copy
    is overwritten with the multi shape (recolored to the multi color). Both
    shapes share the same bounding-box dimensions, and are anchored at each
    component's bounding-box top-left.
    """
    H, W = len(input_grid), len(input_grid[0])
    colors = sorted({v for row in input_grid for v in row if v != 0})

    # Identify the two roles by component count.
    color_comps = {col: _components(input_grid, col) for col in colors}
    multi = next(c for c in colors if len(color_comps[c]) > 1)
    single = next(c for c in colors if len(color_comps[c]) == 1)

    multi_shape = _norm(color_comps[multi][0])
    single_shape = _norm(color_comps[single][0])

    T = {}

    def stamp(component, rel_shape, new_color):
        r0 = min(r for r, c in component)
        c0 = min(c for r, c in component)
        # clear the original cells
        for (r, c) in component:
            T[(r, c)] = 0
        # draw the new shape at the same anchor
        for (dr, dc) in rel_shape:
            r, c = r0 + dr, c0 + dc
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = new_color

    # multi copies receive the single's shape (recolored to single)
    for comp in color_comps[multi]:
        stamp(comp, single_shape, single)
    # the single copy receives the multi shape (recolored to multi)
    stamp(color_comps[single][0], multi_shape, multi)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
