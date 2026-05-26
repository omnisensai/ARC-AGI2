"""Canonical ARC solver for puzzle e5790162.

Rule (inferred from input structure):
  - The grid contains a single START cell colored 3, some TURN markers
    colored 8 and 6, on a background of 0.
  - A path (drawn in color 3) starts at the 3 cell heading RIGHT and
    advances one cell at a time over background cells.
  - When the cell directly ahead holds a marker, the path turns 90 degrees
    WITHOUT consuming the marker cell:
        * marker 8  -> turn LEFT  (counter-clockwise)
        * marker 6  -> turn RIGHT (clockwise)
  - The path keeps going (snaking through any chain of markers) until it
    would step off the grid edge.

infer_T traces this path and returns a latent mask {(r,c): 3} of the
background cells that become 3.  apply_T copies the input and overwrites
only those masked cells (markers and the original 3 are left untouched).
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    start = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 3:
                start = (r, c)
                break
        if start is not None:
            break

    T = {}
    if start is None:
        return T

    cur = start
    dr, dc = 0, 1  # initial heading: right
    max_steps = H * W * 4 + 4
    for _ in range(max_steps):
        nr, nc = cur[0] + dr, cur[1] + dc
        if not (0 <= nr < H and 0 <= nc < W):
            break  # ran off the edge -> done
        v = input_grid[nr][nc]
        if v == 8:
            # turn left (counter-clockwise), do not enter the marker cell
            dr, dc = -dc, dr
            continue
        if v == 6:
            # turn right (clockwise), do not enter the marker cell
            dr, dc = dc, -dr
            continue
        if v == 3:
            # already part of the original start; just advance past it
            cur = (nr, nc)
            continue
        # background cell -> paint it and advance the head
        T[(nr, nc)] = 3
        cur = (nr, nc)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), val in T.items():
        out[r][c] = val
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
