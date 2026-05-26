"""Canonical latent-T solver for ARC puzzle e39e9282.

Structure: the grid contains 3x3 monochrome blocks (color 5 or 6) on a
background. Adjacent to each block edge are 9-markers (single cells just
outside the 3x3 perimeter, aligned with one of the block's rows/columns).

Rule per block:
  * color-6 block ("keeps shape"): the block stays. Each adjacent marker is
    projected perpendicular into the block; it lands on the *center line*
    (center row for U/D markers, center column for L/R markers) at the marker's
    aligned row/column. That landed cell becomes 9. The marker cell is erased.
  * color-5 block ("vanishes"): the whole block becomes background. Each
    adjacent marker projects into the block and lands on the *near edge* cell
    (the block cell closest to the marker) on the marker's aligned line, which
    becomes 9. The marker cell itself is kept (stays 9).

infer_T builds a latent mask {(r,c): new_color}; apply_T overwrites only those
cells on a copy of the input.
"""

MARKER = 9


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_blocks(grid):
    """Return list of (r, c, color) for every 3x3 monochrome block of 5 or 6."""
    H, W = len(grid), len(grid[0])
    blocks = []
    for r in range(H - 2):
        for c in range(W - 2):
            color = grid[r][c]
            if color in (5, 6) and all(
                grid[r + i][c + j] == color for i in range(3) for j in range(3)
            ):
                blocks.append((r, c, color))
    return blocks


def _markers_for(grid, r, c):
    """Markers just outside the 3x3 block perimeter, aligned with a row/col.

    Yields (side, offset) where side in {L,R,U,D} and offset in 0..2 is the
    aligned row index (for L/R) or column index (for U/D)."""
    H, W = len(grid), len(grid[0])
    out = []
    for i in range(3):
        if c - 1 >= 0 and grid[r + i][c - 1] == MARKER:
            out.append(("L", i))
        if c + 3 < W and grid[r + i][c + 3] == MARKER:
            out.append(("R", i))
    for j in range(3):
        if r - 1 >= 0 and grid[r - 1][c + j] == MARKER:
            out.append(("U", j))
        if r + 3 < H and grid[r + 3][c + j] == MARKER:
            out.append(("D", j))
    return out


def infer_T(input_grid):
    bg = _background(input_grid)
    T = {}

    for (r, c, color) in _find_blocks(input_grid):
        markers = _markers_for(input_grid, r, c)

        if color == 6:
            # Block stays; markers project to the center line; markers erased.
            for side, off in markers:
                if side in ("L", "R"):
                    # aligned row = off, land on center column
                    T[(r + off, c - 1 if side == "L" else c + 3)] = bg  # erase marker
                    T[(r + off, c + 1)] = MARKER
                else:  # U / D: aligned column = off, land on center row
                    T[(r - 1 if side == "U" else r + 3, c + off)] = bg
                    T[(r + 1, c + off)] = MARKER
        else:  # color == 5
            # Whole block erased to background; markers kept; near-edge -> 9.
            for i in range(3):
                for j in range(3):
                    T[(r + i, c + j)] = bg
            for side, off in markers:
                if side == "L":
                    T[(r + off, c)] = MARKER       # near edge = left column
                elif side == "R":
                    T[(r + off, c + 2)] = MARKER    # near edge = right column
                elif side == "U":
                    T[(r, c + off)] = MARKER        # near edge = top row
                else:  # D
                    T[(r + 2, c + off)] = MARKER    # near edge = bottom row
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
