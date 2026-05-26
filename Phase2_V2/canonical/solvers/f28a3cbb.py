"""Canonical solver for ARC puzzle f28a3cbb.

Structure of every grid (9x9, background 6):
  - Two solid 3x3 "anchor" blocks of two distinct non-background colors,
    one nestled in a corner near the top-left, one near the bottom-right.
  - Several scattered single cells of those same two colors elsewhere.

Transformation:
  - All scattered cells are cleared back to background.
  - Each anchor block grows along the L-shaped border just outside it
    (the row and column immediately adjacent on the side facing the grid
    interior). Each scattered cell of a block's color is "folded" onto that
    border: if the cell lies more toward the block's open-row direction it
    lands on the new row, otherwise on the new column; its other coordinate
    (clamped into the block's 3-wide span) selects the position.

infer_T builds a latent mask {(r,c): new_color} of every cell that changes
(scattered cells -> background, plus newly grown block cells). apply_T copies
the input and overwrites only the masked cells.
"""


def _find_block(grid, color):
    """Return (r, c) top-left of a solid 3x3 block of `color`, or None."""
    H, W = len(grid), len(grid[0])
    for r in range(H - 2):
        for c in range(W - 2):
            if all(grid[r + i][c + j] == color for i in range(3) for j in range(3)):
                return (r, c)
    return None


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # the anchor colors are the non-background colors
    colors = [v for v in counts if v != bg]

    T = {}

    for color in colors:
        block = _find_block(input_grid, color)
        if block is None:
            continue
        br, bc = block
        # scattered cells of this color (outside its 3x3 block)
        scattered = [
            (r, c)
            for r in range(H)
            for c in range(W)
            if input_grid[r][c] == color
            and not (br <= r < br + 3 and bc <= c < bc + 3)
        ]
        # clear scattered cells
        for (r, c) in scattered:
            T[(r, c)] = bg

        # Determine the growth direction of this block (toward interior).
        # If the block touches the top edge it grows downward (new row below)
        # and rightward (new col to the right); if it touches the bottom edge
        # it grows upward and leftward.
        grow_down = (br == 0)
        new_row = br + 3 if grow_down else br - 1
        grow_right = (bc == 0)
        new_col = bc + 3 if grow_right else bc - 1

        for (r, c) in scattered:
            # signed distance of the cell beyond the block on each axis,
            # measured along the block's open (interior) directions.
            if grow_down:
                d_row = max(0, r - (br + 2))   # how far below the block
            else:
                d_row = max(0, (br) - r)       # how far above the block
            if grow_right:
                d_col = max(0, c - (bc + 2))   # how far right of the block
            else:
                d_col = max(0, (bc) - c)       # how far left of the block

            if d_col > d_row:
                # fold onto the new column; row clamped into block span
                rr = min(max(r, br), br + 2)
                T[(rr, new_col)] = color
            else:
                # fold onto the new row; col clamped into block span
                cc = min(max(c, bc), bc + 2)
                T[(new_row, cc)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
