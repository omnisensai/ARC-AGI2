"""Canonical solver for ARC puzzle 5e6bbc0b.

Rule (derived from ALL pairs):
  The input is a checkerboard of 1s and 0s with a single 8 sitting on one
  edge.  The 8 defines a gravity direction pointing from its edge into the
  grid.  Each line perpendicular to that edge (a row when the 8 is on the
  left/right edge, a column when it is on the top/bottom edge) is rewritten:

    - For every line NOT containing the 8: slide all of its 1s flush against
      the 8's edge; the remaining far cells become 0.
    - For the line CONTAINING the 8: the 8 stays on its edge cell, then the
      line's 1s pile next to it (count = number of 1s in that line), then an
      equal number of 9s pile at the far end, and any leftover cells are 0.

infer_T builds a latent mask {(r, c): new_color} describing exactly which
cells change and to what; apply_T overlays it onto a copy of the input.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Locate the unique 8 marker and the edge it sits on.
    er = ec = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 8:
                er, ec = r, c
    if er is None:
        return {}

    horizontal = (ec == 0 or ec == W - 1)  # 8 on left/right -> rows slide

    T = {}

    if horizontal:
        toward_left = (ec == 0)
        for r in range(H):
            ones = sum(1 for c in range(W) if input_grid[r][c] == 1)
            # Build the target colors in edge-inward order.
            seq = []
            if r == er:
                seq = [8] + [1] * ones + [9] * ones
                seq += [0] * (W - len(seq))
            else:
                seq = [1] * ones + [0] * (W - ones)
            # Place sequence from the 8's edge inward.
            for i in range(W):
                col = i if toward_left else (W - 1 - i)
                T[(r, col)] = seq[i]
    else:
        toward_top = (er == 0)
        for c in range(W):
            ones = sum(1 for r in range(H) if input_grid[r][c] == 1)
            seq = []
            if c == ec:
                seq = [8] + [1] * ones + [9] * ones
                seq += [0] * (H - len(seq))
            else:
                seq = [1] * ones + [0] * (H - ones)
            for i in range(H):
                row = i if toward_top else (H - 1 - i)
                T[(row, c)] = seq[i]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
