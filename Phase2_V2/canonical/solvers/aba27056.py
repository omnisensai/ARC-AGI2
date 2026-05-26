"""Canonical solver for ARC puzzle aba27056.

Rule (water/fountain through a container with gaps):
  - The grid contains one hollow rectangular "container" drawn in a single
    non-background color (the frame). Its interior (background cells strictly
    inside the frame's bounding box) is flooded with color 4.
  - Each side of the frame's bounding box may have a "gap" (a contiguous run of
    background cells where the wall is missing). Water escapes through every gap
    in the outward-perpendicular direction as a 3-fold spray:
        * straight rays from every gap cell going outward to the grid edge,
        * one diagonal ray from the gap's near edge spreading outward by one
          lateral cell per step in each of the two perpendicular directions
          (left/right of a vertical exit, up/down of a horizontal exit).
  - All newly painted cells (interior fill + gap cells + sprays) become 4.
    The frame color is never overwritten.

Canonical latent-T form: infer_T builds an explicit {(r,c): color} mask from the
input structure alone; apply_T copies the input and overwrites only masked cells.
"""

FILL = 4


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    nonbg = [v for v in counts if v != bg]

    T = {}
    if not nonbg:
        return T
    # frame color: the dominant non-background color
    bc = max(nonbg, key=lambda v: counts[v])

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == bc]
    minr = min(r for r, c in cells)
    maxr = max(r for r, c in cells)
    minc = min(c for r, c in cells)
    maxc = max(c for r, c in cells)

    # 1) flood the interior (background cells strictly inside the bbox)
    for r in range(minr + 1, maxr):
        for c in range(minc + 1, maxc):
            if input_grid[r][c] == bg:
                T[(r, c)] = FILL

    # 2) sprays through gaps on each side of the bbox perimeter
    sides = [
        ([(minr, c) for c in range(minc, maxc + 1)], (-1, 0)),  # top, exit up
        ([(maxr, c) for c in range(minc, maxc + 1)], (1, 0)),   # bottom, exit down
        ([(r, minc) for r in range(minr, maxr + 1)], (0, -1)),  # left, exit left
        ([(r, maxc) for r in range(minr, maxr + 1)], (0, 1)),   # right, exit right
    ]

    def emit(gap_cells, ddir):
        dr, dc = ddir
        if dr != 0:  # vertical exit -> lateral axis is column
            lat = sorted(c for r, c in gap_cells)
            wall_coord = gap_cells[0][0]
        else:        # horizontal exit -> lateral axis is row
            lat = sorted(r for r, c in gap_cells)
            wall_coord = gap_cells[0][1]
        lo, hi = lat[0], lat[-1]

        # gap cells (the open wall) themselves fill
        for (r, c) in gap_cells:
            T[(r, c)] = FILL

        d = 1
        while True:
            laterals = set(range(lo, hi + 1))   # straight rays
            laterals.add(lo - d)                # diagonal toward low side
            laterals.add(hi + d)                # diagonal toward high side
            for p in laterals:
                if dr != 0:
                    r = wall_coord + d * dr
                    c = p
                else:
                    r = p
                    c = wall_coord + d * dc
                if 0 <= r < H and 0 <= c < W and input_grid[r][c] == bg:
                    T[(r, c)] = FILL
            d += 1
            # straight ray reaches the edge last among this depth, so stop there
            if dr != 0:
                if not (0 <= wall_coord + d * dr < H):
                    break
            else:
                if not (0 <= wall_coord + d * dc < W):
                    break

    for perim, ddir in sides:
        run = []
        for (r, c) in perim:
            if input_grid[r][c] == bg:
                run.append((r, c))
            elif run:
                emit(run, ddir)
                run = []
        if run:
            emit(run, ddir)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
