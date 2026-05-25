def _panel_shape(cells):
    """Classify a 3x3 panel (list of 9 ints) by the geometric arrangement
    of its marker (5) cells. Returns a shape key independent of color."""
    pts = frozenset((i // 3, i % 3) for i, v in enumerate(cells) if v == 5)
    n = len(pts)
    if n == 1 and pts == {(1, 1)}:
        return "center"
    if pts == {(0, 0), (0, 1), (0, 2)}:
        return "top_row"
    if pts == {(2, 0), (2, 1), (2, 2)}:
        return "bottom_row"
    if pts == {(0, 2), (1, 1), (2, 0)}:
        return "anti_diag"
    if n == 8 and (1, 1) not in pts:
        return "ring"
    return None


# Color assigned to each distinguishable panel shape (derived from the
# task's panel structure, not from grid position).
_SHAPE_COLOR = {
    "center": 4,
    "top_row": 6,
    "bottom_row": 1,
    "anti_diag": 9,
    "ring": 3,
}


def infer_T(input_grid):
    """Build a latent mask: for each 3x3 panel, the solid fill color that
    the panel's marker-shape maps to. T[r][c] = color or None."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    n_panels = W // 3
    for p in range(n_panels):
        c0 = 3 * p
        cells = [input_grid[r][c0 + c] for r in range(3) for c in range(3)]
        shape = _panel_shape(cells)
        if shape is None:
            continue
        color = _SHAPE_COLOR.get(shape)
        if color is None:
            continue
        for r in range(3):
            for c in range(3):
                T[r][c0 + c] = color
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
