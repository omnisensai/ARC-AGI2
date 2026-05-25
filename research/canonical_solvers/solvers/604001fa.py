def _components(grid, color):
    """Return list of 8-connected components of cells equal to `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    res = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
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
                res.append(cells)
    return res


# A 7-marker is an L-tromino: a 2x2 square with exactly one corner missing.
# The missing corner selects the recolor applied to the associated 1-shape.
_MARKER_TO_COLOR = {
    frozenset([(0, 1), (1, 0), (1, 1)]): 3,  # missing top-left
    frozenset([(0, 0), (0, 1), (1, 0)]): 6,  # missing bottom-right
    frozenset([(0, 0), (0, 1), (1, 1)]): 4,  # missing bottom-left
    frozenset([(0, 0), (1, 0), (1, 1)]): 8,  # missing top-right
}


def infer_T(input_grid):
    """Build a {(r,c): new_color} mask.

    Each cluster of 7s is an L-tromino whose missing corner maps to a color.
    Each such marker is matched to its nearest cluster of 1s; every cell of
    that 1-shape is recolored to the marker's color, and the marker cells are
    erased (set to 0).
    """
    H, W = len(input_grid), len(input_grid[0])
    markers = _components(input_grid, 7)
    shapes = _components(input_grid, 1)
    used = [False] * len(shapes)
    T = {}

    for cl in markers:
        rs = [a for a, b in cl]
        cs = [b for a, b in cl]
        mr, mc = min(rs), min(cs)
        norm = frozenset((a - mr, b - mc) for a, b in cl)
        color = _MARKER_TO_COLOR.get(norm)
        # erase the marker
        for a, b in cl:
            T[(a, b)] = 0
        if color is None:
            continue
        # find nearest unused 1-shape (min cell-to-cell Manhattan distance)
        best = None
        best_d = None
        for si, sc in enumerate(shapes):
            if used[si]:
                continue
            d = min(abs(a - x) + abs(b - y) for a, b in cl for x, y in sc)
            if best_d is None or d < best_d:
                best_d = d
                best = si
        if best is None:
            continue
        used[best] = True
        for x, y in shapes[best]:
            T[(x, y)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
