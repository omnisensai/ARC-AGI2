"""Canonical solver for ARC puzzle ac605cbb.

Rule
----
On a blank (0) background there are colored seed markers. Each marker color
emits a fixed directional "ray" of 5s ending in a colored cap:

  color 6 -> ray UP    : 5 cells of 5, then a 6 cap (6 cells above the seed).
  color 3 -> ray DOWN  : 2 cells of 5, then a 3 cap (3 cells below the seed).
  color 1 -> ray RIGHT : 2 cells of 5, then a 1 cap one row up at the ray tip.
  color 2 -> ray LEFT  : 3 cells of 5, then a 2 cap (4 cells left of the seed).

Wherever a horizontal ray (color 2) crosses a vertical ray (color 3/6), the
crossing cell becomes 4 and a diagonal of 4s extends down-left from the
crossing to the grid edge.

infer_T builds the explicit overwrite mask {(r,c): color}; apply_T copies the
input and writes only the masked cells.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    markers = [(r, c, input_grid[r][c])
               for r in range(H) for c in range(W) if input_grid[r][c] != 0]

    # Per-marker stamp: list of ((dr, dc), color) relative to the seed marker.
    STAMP = {
        6: [((-1, 0), 5), ((-2, 0), 5), ((-3, 0), 5),
            ((-4, 0), 5), ((-5, 0), 5), ((-6, 0), 6)],   # ray up, cap 6
        3: [((1, 0), 5), ((2, 0), 5), ((3, 0), 3)],       # ray down, cap 3
        1: [((0, 1), 5), ((0, 2), 5), ((-1, 2), 1)],      # ray right, cap 1
        2: [((0, -1), 5), ((0, -2), 5), ((0, -3), 5),
            ((0, -4), 2)],                                # ray left, cap 2
    }

    T = {}
    horiz5 = set()   # 5-cells laid down by horizontal (color 2) rays
    vert5 = set()    # 5-cells laid down by vertical (color 3 / 6) rays

    for (r, c, col) in markers:
        if col not in STAMP:
            continue
        for (dr, dc), val in STAMP[col]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W:
                T[(rr, cc)] = val
                if val == 5:
                    if col == 2:
                        horiz5.add((rr, cc))
                    elif col in (3, 6):
                        vert5.add((rr, cc))

    # Crossings of a horizontal and a vertical ray spawn a down-left 4 diagonal.
    for (cr, cc) in (horiz5 & vert5):
        rr, c2 = cr, cc
        while 0 <= rr < H and 0 <= c2 < W:
            T[(rr, c2)] = 4
            rr += 1
            c2 -= 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
