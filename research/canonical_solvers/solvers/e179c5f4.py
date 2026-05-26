"""Canonical solver for ARC puzzle e179c5f4.

Rule: A single colored marker (the "ball") sits on a corner of an all-zero
grid. The ball travels along the long axis of the grid, bouncing off the side
walls like a light ray (vertical velocity constant, horizontal velocity flips
at each wall). Every cell the ball visits keeps the marker color; all other
cells become 8.
"""


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Locate the marker (the only non-zero cell), its position and color.
    start = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                start = (r, c, input_grid[r][c])
    if start is None:
        return [[None] * W for _ in range(H)]
    sr, sc, color = start

    # Vertical travel direction: away from the edge the marker sits on.
    vr = -1 if sr == H - 1 else 1
    # Horizontal travel direction: into the interior.
    vc = 1 if sc == 0 else -1

    T = [[None] * W for _ in range(H)]
    r, c = sr, sc
    T[r][c] = color
    while True:
        nr = r + vr
        nc = c + vc
        # Reflect off left/right walls.
        if nc < 0 or nc >= W:
            vc = -vc
            nc = c + vc
        # Stop when we run past the top/bottom.
        if nr < 0 or nr >= H:
            break
        r, c = nr, nc
        T[r][c] = color

    # All cells not on the ball's path become 8.
    for rr in range(H):
        for cc in range(W):
            if T[rr][cc] is None:
                T[rr][cc] = 8
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
