def _components(grid):
    """Connected components (8-connectivity) of equal nonzero color."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and (r, c) not in seen:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((a + dr, b + dc))
                comps.append((color, cells))
    return comps


def _norm(cells):
    """Normalized shape signature (translate to origin)."""
    mr = min(a for a, b in cells)
    mc = min(b for a, b in cells)
    return frozenset((a - mr, b - mc) for a, b in cells)


def infer_T(input_grid):
    """Latent mask: recolor each marker (color 1) shape to the color of the
    non-marker colored shape having the identical normalized form."""
    comps = _components(input_grid)
    palette = {}          # normalized shape -> colored shape's color
    markers = []          # (cells, normalized shape) for color-1 components
    for color, cells in comps:
        n = _norm(cells)
        if color == 1:
            markers.append((cells, n))
        else:
            palette.setdefault(n, color)
    T = {}
    for cells, n in markers:
        new_color = palette.get(n)
        if new_color is not None:
            for (a, b) in cells:
                T[(a, b)] = new_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
