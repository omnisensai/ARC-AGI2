def infer_T(input_grid):
    """Infer a latent mask: a hollow rectangle in the box color whose four edges
    sit one cell inward from the four color-5 markers surrounding the box."""
    H, W = len(input_grid), len(input_grid[0])
    # Markers are color 5 (four isolated cells around the inner box).
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    # Box color: the lone non-background (0), non-marker (5) color.
    box_color = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v != 5:
                box_color = v
                break
        if box_color is not None:
            break
    T = {}
    if not markers or box_color is None:
        return T
    rows = [r for r, c in markers]
    cols = [c for r, c in markers]
    top = min(rows) + 1
    bottom = max(rows) - 1
    left = min(cols) + 1
    right = max(cols) - 1
    for c in range(left, right + 1):
        T[(top, c)] = box_color
        T[(bottom, c)] = box_color
    for r in range(top, bottom + 1):
        T[(r, left)] = box_color
        T[(r, right)] = box_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
