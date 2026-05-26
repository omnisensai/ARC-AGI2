"""Canonical latent-T solver for ARC puzzle dd2401ed.

Structure of every pair:
  - A full vertical line of color 5 splits the grid into a left band (which
    holds scattered marker cells of color 1) and a right region (scattered
    cells of color 2).
  - The line is mirrored across itself: a left band of width ``line_col``
    reflects to occupy the columns just right of the line, so the line ends
    up at ``2*line_col + 1``.  The old line cells become background (0).
  - The columns the line sweeps over (the open interval between the old and
    new line) become "1-territory": every color-2 cell sitting in that zone
    flips to color 1.  This flip only fires when the left band actually
    carries enough markers (>= 3 color-1 cells); with fewer markers the line
    moves but no 2 is recolored.
  - Markers (1) and untouched 2s keep their positions.

T is expressed as a sparse latent mask {(r, c): new_color}; apply_T copies the
input and overwrites only those cells.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # Locate the single full vertical line of color 5.
    line_col = None
    for c in range(W):
        if all(input_grid[r][c] == 5 for r in range(H)):
            line_col = c
            break

    T = {}
    if line_col is None:
        return T

    # Mirror the left band across the line: new line at 2*line_col + 1.
    new_col = 2 * line_col + 1
    if new_col >= W:
        new_col = W - 1

    # Count the markers (color 1) carried by the left band.
    marker_count = sum(
        1 for r in range(H) for c in range(W) if input_grid[r][c] == 1
    )

    # Erase the old line and draw the relocated line.
    for r in range(H):
        if line_col != new_col:
            T[(r, line_col)] = 0
        T[(r, new_col)] = 5

    # The swept zone becomes 1-territory; recolor 2 -> 1 there, but only when
    # the band carries at least three markers.
    if marker_count >= 3:
        for r in range(H):
            for c in range(line_col + 1, new_col):
                if input_grid[r][c] == 2:
                    T[(r, c)] = 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
