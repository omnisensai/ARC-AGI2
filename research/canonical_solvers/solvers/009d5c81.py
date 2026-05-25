def _normalize(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


# Marker shape (made of 1s) -> color to paint the 8-figure.
_SHAPE_COLOR = {
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1)): 7,
    ((0, 0), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)): 3,
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)): 2,
}


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # The marker is the group of 1s; its shape selects the paint color.
    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    color = None
    if ones:
        color = _SHAPE_COLOR.get(_normalize(ones))
    T = {}
    if color is not None:
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] == 8:
                    T[(r, c)] = color
    # Remove the marker cells.
    for (r, c) in ones:
        T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
