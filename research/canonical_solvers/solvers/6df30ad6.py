"""Canonical solver for ARC puzzle 6df30ad6.

Rule: the grid contains one shape made of color-5 cells plus scattered
single-cell "noise" pixels in several other colors. The shape is recolored
with the noise color whose pixel lies closest to the shape (king-move /
Chebyshev distance to the nearest 5-cell, Manhattan distance as tie-break),
and every noise pixel is erased to background (0).
"""

SHAPE_COLOR = 5
BG = 0


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == color]
    return cells


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])

    shape_cells = []
    noise = {}  # color -> list of (r,c)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == BG:
                continue
            if v == SHAPE_COLOR:
                shape_cells.append((r, c))
            else:
                noise.setdefault(v, []).append((r, c))

    T = {}
    if not shape_cells:
        return T

    # Pick the noise color whose nearest pixel is closest to the shape.
    best_color = None
    best_key = None
    for color, pts in noise.items():
        cheb = min(max(abs(r - fr), abs(c - fc))
                   for (r, c) in pts for (fr, fc) in shape_cells)
        manh = min(abs(r - fr) + abs(c - fc)
                   for (r, c) in pts for (fr, fc) in shape_cells)
        key = (cheb, manh)
        if best_key is None or key < best_key:
            best_key = key
            best_color = color

    # Recolor the shape cells with the chosen color.
    if best_color is not None:
        for (r, c) in shape_cells:
            T[(r, c)] = best_color

    # Erase every noise pixel.
    for pts in noise.values():
        for (r, c) in pts:
            T[(r, c)] = BG

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
