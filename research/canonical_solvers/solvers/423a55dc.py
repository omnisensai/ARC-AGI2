"""Canonical solver for ARC puzzle 423a55dc.

Rule: A single non-background shape sits on the grid. The shape is vertically
sheared to the left: each colored cell at row r is shifted LEFT by (maxr - r)
columns, where maxr is the bottom-most row of the shape (its bottom row stays
put, and rows higher up move progressively further left). Cells pushed past the
left edge (column < 0) are dropped. The original shape footprint is cleared to
background first; sheared cells are then written on top.
"""


def infer_T(input_grid):
    """Compute the latent change mask {(r, c): new_color} from the input alone."""
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c, input_grid[r][c])
             for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    if not cells:
        return {}
    maxr = max(r for r, c, v in cells)

    # First clear the entire shape footprint to background.
    clears = {(r, c): 0 for r, c, v in cells}

    # Then place each cell sheared left by its depth above the bottom row.
    places = {}
    for r, c, v in cells:
        nc = c - (maxr - r)
        if 0 <= nc < W:
            places[(r, nc)] = v

    # Placements take precedence over clears at any shared coordinate.
    T = dict(clears)
    T.update(places)
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the mask."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
