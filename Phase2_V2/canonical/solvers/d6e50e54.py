"""Canonical latent-T solver for ARC puzzle d6e50e54.

Rule (inferred from all train+test pairs):
  - The grid contains one solid rectangle of color 1 on a background of 7,
    plus several scattered 9 markers, each aligned (by row or column) with
    the rectangle's span.
  - Recolor the rectangle from 1 -> 2.
  - Each 9 marker slides straight toward the rectangle along its shared
    row (if it lies within the rectangle's row span) or column (if within
    the column span).  Let `dist` be the gap distance from the marker to
    the near edge of the rectangle, and `span` the rectangle's extent along
    the direction of motion.
      * if dist <  span : the marker lands ON the rectangle's edge cell
                          (one cell inside the bounding box).
      * if dist >= span : the marker lands ONE cell OUTSIDE the edge.
  - All cells the markers vacate revert to background (7); the rectangle
    interior is 2 except where a marker now sits.

infer_T builds the latent mask {(r,c): new_color} describing exactly which
cells change; apply_T overwrites only those cells.
"""

BG = 7
RECT = 1
MARK = 9
NEW_RECT = 2


def _find_rect(grid):
    H, W = len(grid), len(grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == RECT]
    if not cells:
        return None
    r0 = min(r for r, c in cells)
    r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells)
    c1 = max(c for r, c in cells)
    return r0, r1, c0, c1


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    rect = _find_rect(input_grid)
    if rect is None:
        return T
    r0, r1, c0, c1 = rect
    height = r1 - r0 + 1
    width = c1 - c0 + 1

    # 1) recolor the rectangle interior 1 -> 2
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if input_grid[r][c] == RECT:
                T[(r, c)] = NEW_RECT

    # 2) slide each 9 marker toward the rectangle
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] == MARK]

    for (r, c) in markers:
        # marker vacates its original cell -> background
        # (will be overwritten below if it lands here, which it won't)
        T[(r, c)] = BG

        within_cols = c0 <= c <= c1
        within_rows = r0 <= r <= r1

        if within_cols and not within_rows:
            # vertical movement; motion span = rectangle height
            span = height
            if r < r0:                       # approaching from above
                dist = r0 - r
                nr = r0 if dist < span else r0 - 1
            else:                            # approaching from below
                dist = r - r1
                nr = r1 if dist < span else r1 + 1
            nc = c
        elif within_rows and not within_cols:
            # horizontal movement; motion span = rectangle width
            span = width
            if c < c0:                       # approaching from the left
                dist = c0 - c
                nc = c0 if dist < span else c0 - 1
            else:                            # approaching from the right
                dist = c - c1
                nc = c1 if dist < span else c1 + 1
            nr = r
        else:
            # not aligned with the rectangle span: leave in place
            nr, nc = r, c

        T[(nr, nc)] = MARK

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
