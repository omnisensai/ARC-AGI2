"""Canonical solver for ARC puzzle fd02da9e.

Each non-background pixel sits in one of the four grid corners. Depending on
whether the corner is on the top or bottom edge, the pixel "blooms" into a fixed
shape pulled toward the grid center, drawn in the pixel's own color:

  * top corners    -> a 2x2 block placed just inside, near the vertical center.
  * bottom corners -> a 3-cell "leg" (two stacked cells plus a diagonal foot).

The shape is defined by signed offsets relative to the corner pixel and is
mirrored horizontally for right-edge corners, so the rule is purely structural
(no hardcoded absolute coordinates).
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    """Return latent mask {(r, c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)

    # Shape templates as (row_offset, col_offset) relative to the corner pixel,
    # written for a LEFT corner. Right corners mirror col offsets.
    top_block = [(1, 1), (1, 2), (2, 1), (2, 2)]   # 2x2 pulled inward
    bottom_leg = [(-3, 2), (-2, 2), (-1, 3)]        # stacked cells + diagonal foot

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            top = (r == 0)
            left = (c == 0)
            offsets = top_block if top else bottom_leg
            for dr, dc in offsets:
                rr = r + dr
                cc = c + (dc if left else -dc)
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
