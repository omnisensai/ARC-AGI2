"""Canonical solver for ARC puzzle d9f24cd1.

Rule (inferred from structure of input alone):
  - The bottom row contains 2-colored "emitter" markers.
  - From each emitter, a vertical ray of color 2 travels upward.
  - 5-colored cells act as obstacles: when the ray's next cell above (in its
    current column) is a 5, the ray cannot pass. It stops just below the 5 and
    bends one column to the right (filling the corner cell), then continues
    travelling upward in the new column from the same row.
  - This may chain if the new column also has a 5 above.
  - The 5 cells themselves are preserved.
"""


def infer_T(input_grid):
    """Return a latent mask dict {(r, c): new_color} of cells to overwrite."""
    H = len(input_grid)
    W = len(input_grid[0])
    T = {}
    fives = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] == 5
    )
    for c in range(W):
        if input_grid[H - 1][c] != 2:
            continue
        r, col = H - 1, c
        T[(r, col)] = 2
        while r > 0:
            if (r - 1, col) in fives:
                # blocked above: bend right at this row, then keep climbing
                if col + 1 < W:
                    col = col + 1
                    T[(r, col)] = 2
                else:
                    break
            else:
                r = r - 1
                T[(r, col)] = 2
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
