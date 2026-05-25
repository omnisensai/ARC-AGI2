"""Canonical solver for ARC puzzle 11dc524f.

Rule (same-size grid, background 7):
  The grid holds two objects: a 2x2 square of color 5, and a 4-cell shape of
  color 2. The two objects are separated along exactly one axis (either left/
  right or up/down). The 2-shape slides along that axis until it is adjacent to
  the inner face of the 5 square, keeping its shape. The 5 square is then
  replaced by the mirror image of the relocated 2-shape, reflected across the
  contact line between the two objects. The result is a mirror-symmetric pair
  of objects (2 on its original side, 5 on its original side) touching along
  that line. All other cells are untouched.

infer_T computes the latent mask: a dict {(r,c): new_color} listing every cell
that must change (cells cleared back to background plus the relocated/mirrored
object cells). apply_T copies the input and overwrites only masked cells.
"""


def _cells(grid, v):
    return [(r, c) for r, row in enumerate(grid)
            for c, x in enumerate(row) if x == v]


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    c2 = _cells(input_grid, 2)
    c5 = _cells(input_grid, 5)
    T = {}
    if not c2 or not c5:
        return T, bg

    # clear the original object cells
    for r, c in c2 + c5:
        T[(r, c)] = bg

    col2 = [c for _, c in c2]
    col5 = [c for _, c in c5]
    row2 = [r for r, _ in c2]
    row5 = [r for r, _ in c5]
    minc2, maxc2 = min(col2), max(col2)
    minc5, maxc5 = min(col5), max(col5)
    minr2, maxr2 = min(row2), max(row2)
    minr5, maxr5 = min(row5), max(row5)

    # are the two objects separated horizontally (no overlapping columns)?
    horiz = (maxc2 < minc5) or (maxc5 < minc2)

    new2 = []
    new5 = []
    if horiz:
        if maxc2 < minc5:            # 2 is to the LEFT of 5
            shift = (minc5 - 1) - maxc2          # bring 2's right edge to minc5-1
            new2 = [(r, c + shift) for r, c in c2]
            axis = 2 * minc5 - 1                 # reflect col across line left of minc5
            new5 = [(r, axis - c) for r, c in new2]
        else:                        # 2 is to the RIGHT of 5
            shift = (maxc5 + 1) - minc2          # bring 2's left edge to maxc5+1
            new2 = [(r, c + shift) for r, c in c2]
            axis = 2 * maxc5 + 1
            new5 = [(r, axis - c) for r, c in new2]
    else:
        if maxr2 < minr5:            # 2 is ABOVE 5
            shift = (minr5 - 1) - maxr2
            new2 = [(r + shift, c) for r, c in c2]
            axis = 2 * minr5 - 1
            new5 = [(axis - r, c) for r, c in new2]
        else:                        # 2 is BELOW 5
            shift = (maxr5 + 1) - minr2
            new2 = [(r + shift, c) for r, c in c2]
            axis = 2 * maxr5 + 1
            new5 = [(axis - r, c) for r, c in new2]

    for r, c in new2:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 2
    for r, c in new5:
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 5
    return T, bg


def apply_T(input_grid, T_bg):
    T, _bg = T_bg
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
