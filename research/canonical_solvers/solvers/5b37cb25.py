"""Canonical solver for ARC puzzle 5b37cb25.

Rule
----
The grid has a 1-cell border frame whose four sides carry four distinct
colors (top = grid[0][1], bottom = grid[-1][1], left = grid[1][0],
right = grid[1][-1]). Inside the frame are blobs drawn in a single "blob"
color over a single interior background color.

Each blob has one or more triangular notches: a wedge of background-colored
cells cut into the blob. The wedge has a single deepest "tip" cell that is a
background cell surrounded on exactly three orthogonal sides by blob cells;
its one remaining orthogonal neighbour is also background and lies in the
direction the notch opens.

For every such tip we draw a plus (+) shape (the cell + its 4 orthogonal
neighbours) centred on that open-side neighbour, painted with the border
colour of the side the notch points toward (up -> top, down -> bottom,
left -> left, right -> right).
"""

from collections import Counter


def infer_T(input_grid):
    """Compute the latent transformation mask as {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])

    # Border colours from the frame.
    top = input_grid[0][1]
    bottom = input_grid[H - 1][1]
    left = input_grid[1][0]
    right = input_grid[1][W - 1]

    # Interior background = most common, blob = second most common.
    cnt = Counter()
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            cnt[input_grid[r][c]] += 1
    most = cnt.most_common()
    bg = most[0][0]
    blob = most[1][0]

    T = {}
    orth = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if input_grid[r][c] != bg:
                continue
            blob_nb = []
            bg_nb = []
            for dr, dc in orth:
                v = input_grid[r + dr][c + dc]
                if v == blob:
                    blob_nb.append((dr, dc))
                elif v == bg:
                    bg_nb.append((dr, dc))
            # A wedge tip: 3 blob neighbours + exactly 1 background neighbour.
            if len(blob_nb) != 3 or len(bg_nb) != 1:
                continue
            dr, dc = bg_nb[0]            # opening direction
            pr, pc = r + dr, c + dc      # plus centre (one step toward opening)
            if dr == -1:
                color = top
            elif dr == 1:
                color = bottom
            elif dc == -1:
                color = left
            else:
                color = right
            for ddr, ddc in ((0, 0),) + orth:
                rr, cc = pr + ddr, pc + ddc
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = color
    return T


def apply_T(input_grid, T):
    """Copy the input, overwriting only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
