"""Canonical solver for ARC task fd4b2b02.

Rule: the input contains a single solid rectangle of one color (3 or 6).
It echoes outward along all four diagonal directions. Each successive echo:
  - swaps its bounding-box dimensions (H<->W),
  - is placed immediately diagonally adjacent to the previous block
    (touching at a corner), and
  - alternates color between the original color and the complementary
    color of the {3, 6} pair (the first echo uses the complementary color).
Echoes continue until they leave the grid.

infer_T computes the set of cells that must be painted (a latent mask
mapping (r, c) -> color); apply_T copies the input and overwrites only
those masked cells.
"""


def _find_object(grid):
    H, W = len(grid), len(grid[0])
    pts = [(r, c) for r in range(H) for c in range(W) if grid[r][c]]
    if not pts:
        return None
    color = grid[pts[0][0]][pts[0][1]]
    rs = [r for r, c in pts]
    cs = [c for r, c in pts]
    return color, min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    obj = _find_object(input_grid)
    T = {}
    if obj is None:
        return T
    color, r0, r1, c0, c1 = obj
    other = 6 if color == 3 else 3

    def paint(col, top, bot, left, right):
        for y in range(max(0, top), min(H, bot + 1)):
            for x in range(max(0, left), min(W, right + 1)):
                T[(y, x)] = col

    # the original rectangle stays as-is (its color) -- include for safety
    paint(color, r0, r1, c0, c1)

    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        cr0, cr1, cc0, cc1 = r0, r1, c0, c1
        for step in range(max(H, W) + 2):
            h = cr1 - cr0 + 1
            w = cc1 - cc0 + 1
            nh, nw = w, h  # swap dimensions

            if dr == 1:
                ntop = cr1 + 1
                nbot = ntop + nh - 1
            else:
                nbot = cr0 - 1
                ntop = nbot - nh + 1
            if dc == 1:
                nleft = cc1 + 1
                nright = nleft + nw - 1
            else:
                nright = cc0 - 1
                nleft = nright - nw + 1

            newcol = other if step % 2 == 0 else color
            paint(newcol, ntop, nbot, nleft, nright)

            cr0, cr1, cc0, cc1 = ntop, nbot, nleft, nright
            if (dr == 1 and ntop > H) or (dr == -1 and nbot < 0) or \
               (dc == 1 and nleft > W) or (dc == -1 and nright < 0):
                break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
