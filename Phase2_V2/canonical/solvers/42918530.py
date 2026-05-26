"""Canonical solver for ARC puzzle 42918530.

Rule: the grid is tiled with 5x5 boxes (each a colored frame with a 3x3
interior), separated by background. Boxes are grouped by their frame color.
Among boxes of the same color, the "template" boxes have a non-empty interior
pattern (frame-color cells inside the 3x3). Boxes of that color whose interior
is empty get their interior filled with the template pattern. Boxes that
already carry a pattern, and colors with no template, are left unchanged.
"""


def _find_boxes(grid):
    """Return list of (r, c) top-left corners of 5x5 boxes."""
    H, W = len(grid), len(grid[0])
    boxes = []
    for r in range(1, H, 6):
        for c in range(1, W, 6):
            if r + 5 <= H and c + 5 <= W:
                # must be a real frame: corner non-background
                if grid[r][c] != 0:
                    boxes.append((r, c))
    return boxes


def _interior_mask(grid, r, c, col):
    """3x3 interior occupancy of frame color `col` for box at (r, c)."""
    return tuple(
        tuple(1 if grid[r + 1 + i][c + 1 + j] == col else 0 for j in range(3))
        for i in range(3)
    )


def infer_T(input_grid):
    """Compute latent mask: {(row, col): new_color} of interior cells to fill."""
    from collections import defaultdict

    boxes = _find_boxes(input_grid)

    # Group boxes by frame color; record interior mask of each.
    groups = defaultdict(list)
    for (r, c) in boxes:
        col = input_grid[r][c]
        groups[col].append((r, c, _interior_mask(input_grid, r, c, col)))

    T = {}
    for col, members in groups.items():
        # Templates = boxes with a non-empty interior pattern.
        templates = [m for m in members if any(any(row) for row in m[2])]
        if not templates:
            continue
        # Canonical pattern: the (shared) non-empty interior pattern.
        template_pat = templates[0][2]
        # Fill every empty-interior box of this color with the template.
        for (r, c, mask) in members:
            if any(any(row) for row in mask):
                continue  # already has a pattern -> leave unchanged
            for i in range(3):
                for j in range(3):
                    if template_pat[i][j]:
                        T[(r + 1 + i, c + 1 + j)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
