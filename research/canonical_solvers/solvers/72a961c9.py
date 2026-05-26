"""Canonical solver for ARC puzzle 72a961c9.

Rule: The grid contains one full horizontal line of 1s with embedded
colored markers (cells that are neither 0 nor 1). From each marker, a
vertical bar grows upward away from the line. The bar's height depends on
the marker color (8 -> 3 cells, 2 -> 4 cells). The bar's topmost cell takes
the marker color; all cells below it (down to the line) are 1s.
"""


def infer_T(input_grid):
    """Compute the latent overwrite mask {(r, c): color} from input structure."""
    H, W = len(input_grid), len(input_grid[0])

    # Locate the full horizontal line: a row entirely filled (no background 0s)
    # that contains the line color 1.
    line_row = None
    for r in range(H):
        row = input_grid[r]
        if all(v != 0 for v in row) and any(v == 1 for v in row):
            line_row = r
            break

    T = {}
    if line_row is None:
        return T

    # Markers are the non-line, non-background cells sitting on the line.
    markers = [(line_row, c, input_grid[line_row][c])
               for c in range(W)
               if input_grid[line_row][c] not in (0, 1)]

    # Bars always grow upward (toward smaller row indices).
    drow = -1

    # Bar height (cells above the line) keyed by marker color.
    height_map = {8: 3, 2: 4}

    for (r, c, color) in markers:
        h = height_map.get(color, 3)
        for i in range(1, h + 1):
            rr = r + drow * i
            if 0 <= rr < H:
                # Topmost cell of the bar takes the marker color; rest are 1.
                T[(rr, c)] = color if i == h else 1

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
