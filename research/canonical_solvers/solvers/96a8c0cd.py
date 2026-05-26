"""Canonical solver for ARC puzzle 96a8c0cd.

Rule: a single source cell of color 2 sitting on a grid edge emits a "laser"
that travels straight into the grid (perpendicular to the edge it sits on).
The interior contains short straight bars (3-cell lines) of color 1 and color 3
oriented perpendicular to the laser's travel. When the laser would run into a
bar it detours AROUND it: it turns aside (LEFT for a color-1 bar, RIGHT for a
color-3 bar), runs parallel to the bar until just past its far end, then resumes
its original heading. The laser keeps going until it leaves the grid. Every cell
the laser visits is painted color 2 (existing 1/3 bars are left untouched).

infer_T traces the laser path from the source and returns the set of visited
cells as the transformation mask (each mapped to color 2). apply_T copies the
input and overwrites only the masked cells.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Locate the single source cell of color 2.
    src = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                src = (r, c)
                break
        if src:
            break
    if src is None:
        return {}

    sr, sc = src
    # Initial heading points away from the edge the source rests on.
    if sc == 0:
        d = (0, 1)
    elif sc == W - 1:
        d = (0, -1)
    elif sr == 0:
        d = (1, 0)
    elif sr == H - 1:
        d = (-1, 0)
    else:
        d = (0, 1)

    def turn_left(v):
        return (-v[1], v[0])

    def turn_right(v):
        return (v[1], -v[0])

    visited = {src}
    r, c = src
    guard = 0
    limit = H * W * 8

    while True:
        guard += 1
        if guard > limit:
            break
        nr, nc = r + d[0], c + d[1]
        if not (0 <= nr < H and 0 <= nc < W):
            break  # laser exits the grid
        cell = input_grid[nr][nc]
        if cell == 0 or cell == 2:
            r, c = nr, nc
            visited.add((r, c))
            continue
        # Obstacle bar ahead: pick detour side by color.
        nd = turn_left(d) if cell == 1 else turn_right(d)
        # Slide sideways while the forward cell is still blocked by a bar.
        while True:
            fr, fc = r + d[0], c + d[1]
            blocked = (0 <= fr < H and 0 <= fc < W and input_grid[fr][fc] in (1, 3))
            if not blocked:
                break
            r, c = r + nd[0], c + nd[1]
            if not (0 <= r < H and 0 <= c < W):
                break
            visited.add((r, c))
        if not (0 <= r < H and 0 <= c < W):
            break

    # Latent mask: every visited cell becomes color 2.
    T = {cell: 2 for cell in visited}
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
