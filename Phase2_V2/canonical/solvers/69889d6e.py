"""Canonical solver for ARC puzzle 69889d6e.

Rule: A single source cell (color 2) emits a 2-wide diagonal "staircase" beam
that travels toward the upper-right. Each diagonal step paints the leading cell
(r-1, c+1) plus the cell to its left (r-1, c), forming the thick staircase.
Obstacle cells (color 1) deflect the beam: whenever the next diagonal step would
land either painted cell onto a `1`, the beam instead steps horizontally to the
right (widening that row) until the up-right path is clear, which shifts the
whole diagonal one column to the right. The beam never paints over a `1`, and
continues until it leaves the grid.

infer_T computes the set of cells the beam paints (the latent mask, all -> 2);
apply_T overwrites only those cells on a copy of the input.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    ones = set(
        (r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1
    )
    src = next(
        ((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2),
        None,
    )
    paint = {}  # latent mask: cell -> new color
    if src is None:
        return paint

    r, c = src
    paint[(r, c)] = 2
    steps = 0
    while steps < 300:
        steps += 1
        nr, nc = r - 1, c + 1  # up-right diagonal target
        if nr < -1:
            break
        lead = (nr, nc)
        left = (nr, nc - 1)
        if lead in ones or left in ones:
            # diagonal blocked by an obstacle: detour horizontally right,
            # which shifts the staircase one column over.
            r, c = r, c + 1
            if 0 <= r < H and 0 <= c < W:
                paint[(r, c)] = 2
            if 0 <= r < H and 0 <= c - 1 < W and (r, c - 1) not in ones:
                paint[(r, c - 1)] = 2
            if c >= W:
                break
            continue
        # normal diagonal step
        r, c = nr, nc
        if 0 <= r < H and 0 <= c < W:
            paint[(r, c)] = 2
        if 0 <= r < H and 0 <= c - 1 < W and (r, c - 1) not in ones:
            paint[(r, c - 1)] = 2
        if r < 0 or c >= W:
            break

    return paint


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
