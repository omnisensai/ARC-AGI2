"""Canonical latent-T solver for ARC puzzle 2bee17df.

Rule
----
The grid is a background of 0 enclosed by a two-colour border (made of 8 and 2)
whose inner edge is jagged with little "teeth" poking into the interior.

A *channel* is a straight corridor of background that runs all the way across the
interior, touching the inner baseline of both opposing borders and crossed by no
border tooth:

  - a vertical channel at column c: the interior reaches the top border at depth 1
    AND the bottom border at depth 1, and the whole column is a single contiguous
    run of background (no border cell interrupts it);
  - a horizontal channel at row r: symmetric condition for the left/right borders.

The latent transformation T marks every background (0) cell that lies on any such
channel; apply_T paints those cells with colour 3.
"""


def _runs_of_zero(arr):
    """Return the runs of background (0) in a 1D sequence."""
    runs = []
    start = None
    for i, v in enumerate(arr):
        if v == 0 and start is None:
            start = i
        elif v != 0 and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(arr) - 1))
    return runs


def infer_T(input_grid):
    """Infer the latent mask of cells to recolour from the input structure."""
    H = len(input_grid)
    W = len(input_grid[0])

    # Depth of the border (number of non-background cells) reached from each side.
    top = [next((d for d in range(H) if input_grid[d][c] == 0), H) for c in range(W)]
    bot = [next((d for d in range(H) if input_grid[H - 1 - d][c] == 0), H) for c in range(W)]
    left = [next((d for d in range(W) if input_grid[r][d] == 0), W) for r in range(H)]
    right = [next((d for d in range(W) if input_grid[r][W - 1 - d] == 0), W) for r in range(H)]

    # Vertical channels: interior touches both top and bottom inner baseline (depth 1)
    # and the column is one uninterrupted background run.
    line_cols = [
        c for c in range(1, W - 1)
        if top[c] == 1 and bot[c] == 1
        and len(_runs_of_zero([input_grid[r][c] for r in range(H)])) == 1
    ]
    # Horizontal channels: symmetric condition on the left/right borders.
    line_rows = [
        r for r in range(1, H - 1)
        if left[r] == 1 and right[r] == 1
        and len(_runs_of_zero(input_grid[r])) == 1
    ]

    line_cols = set(line_cols)
    line_rows = set(line_rows)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0 and (r in line_rows or c in line_cols):
                T[r][c] = 3
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
