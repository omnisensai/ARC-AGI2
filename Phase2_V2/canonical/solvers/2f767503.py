"""Canonical solver for ARC puzzle 2f767503.

Rule
----
A straight line of 5s (3 cells, horizontal or vertical) together with a single
9 placed at the line's centre forms an "arrow". The 9 marks the tail; the arrow
points perpendicular to the line, in the direction AWAY from the 9 (i.e. from
the 9, through the line, and onward).

A single ray is cast from the line centre in that pointing direction. Every
connected component (4-connectivity) of color-4 cells that the ray passes
through is erased entirely (overwritten with the background color 7).

`infer_T` builds the latent mask of cells to overwrite (every cell of every
4-component the ray touches). `apply_T` copies the input and writes 7 into the
masked cells.
"""


def _find_color(grid, color):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == color]


def _component_of(grid, sr, sc, color=4):
    """Full 4-connected component of `color` containing (sr, sc)."""
    H, W = len(grid), len(grid[0])
    comp = set()
    stack = [(sr, sc)]
    while stack:
        r, c = stack.pop()
        if (r, c) in comp:
            continue
        if not (0 <= r < H and 0 <= c < W) or grid[r][c] != color:
            continue
        comp.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    return comp


def infer_T(input_grid):
    """Return a latent mask {(r, c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    fives = _find_color(input_grid, 5)
    nines = _find_color(input_grid, 9)
    if not fives or not nines:
        return T
    nine = nines[0]

    rows = sorted(set(r for r, c in fives))
    cols = sorted(set(c for r, c in fives))
    horizontal = len(rows) == 1  # line lies along a single row

    nr, nc = nine
    if horizontal:
        line_r = rows[0]
        # ray travels vertically, away from the 9, through the 9's column
        step_r = -1 if nr > line_r else 1
        step_c = 0
        start_r, start_c = line_r, nc
    else:
        line_c = cols[0]
        # ray travels horizontally, away from the 9, through the 9's row
        step_c = -1 if nc > line_c else 1
        step_r = 0
        start_r, start_c = nr, line_c

    # Cast the single ray; collect every 4-component it crosses.
    erased = set()
    r, c = start_r + step_r, start_c + step_c
    while 0 <= r < H and 0 <= c < W:
        if input_grid[r][c] == 4 and (r, c) not in erased:
            erased |= _component_of(input_grid, r, c, color=4)
        r += step_r
        c += step_c

    for (rr, cc) in erased:
        T[(rr, cc)] = 7
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
