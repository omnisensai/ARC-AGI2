"""Canonical solver for ARC puzzle e4941b18.

Rule (inferred from all pairs):
  The grid contains a solid rectangular block of color 5 and two single-cell
  markers (color 2 and color 8) sitting in the background just above the block.
  The transformation:
    * The 2-marker slides over to occupy the 8-marker's original cell.
    * The 8-marker slides down to the bottom corner of the block, ending one
      column outside the block on the same horizontal side it started relative
      to the 2 (left of 2 -> bottom-left-outside, right of 2 -> bottom-right-
      outside), at the block's bottom row.
  Both original marker cells are cleared to the background color.
"""


def _find(grid, v):
    cells = []
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == v:
                cells.append((r, c))
    return cells


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    """Return a latent mask dict {(r,c): new_color} of cells to overwrite."""
    grid = input_grid
    bg = _background(grid)

    two = _find(grid, 2)
    eight = _find(grid, 8)
    block = _find(grid, 5)
    if not two or not eight or not block:
        return {}

    (tr, tc) = two[0]
    (er, ec) = eight[0]

    rows = [r for r, c in block]
    cols = [c for r, c in block]
    rmax = max(rows)
    cmin = min(cols)
    cmax = max(cols)

    T = {}
    # Clear original marker cells.
    T[(tr, tc)] = bg
    T[(er, ec)] = bg

    # 2 moves to where 8 was.
    T[(er, ec)] = 2

    # 8 slides to the bottom corner just outside the block, on the side it sits
    # relative to the 2 marker.
    if ec < tc:
        dest_c = cmin - 1
    else:
        dest_c = cmax + 1
    T[(rmax, dest_c)] = 8

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
