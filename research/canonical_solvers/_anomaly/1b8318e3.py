"""Canonical solver for ARC puzzle 1b8318e3.

Rule (same-size grid):
  The grid contains several solid 2x2 blocks of color 5 (fixed anchors) plus a
  number of scattered single colored cells (any non-zero, non-5 color).  Each
  single cell "snaps" onto the nearest 5-block, landing on a cell of that
  block's surrounding ring (the frame one step around the 2x2):

    * If the single shares the block's row band (rows br..br+1) it slides
      horizontally and lands directly beside the block: (r, bc-1) or (r, bc+2).
    * If it shares the block's column band it slides vertically and lands at
      (br-1, c) or (br+2, c).
    * Otherwise (diagonal) it lands on the outside corner of the frame in its
      approach quadrant: row = br-1 (above) / br+2 (below), col = bc-1 (left) /
      bc+2 (right).

  The 5-blocks never move and the single's original cell becomes background.
  Singles are placed nearest-first; if two would land on the same cell the
  closer one wins and the other is re-assigned to its next nearest block.

infer_T builds the latent mask T = {original_single_cell: 0} U
{landing_cell: color}; apply_T copies the input and overwrites masked cells.

Note: this reproduces every pair exactly except a single anomalous pixel in
train pair 0 ((14,8) lands one column inside the expected below-left corner);
all of train pairs 1 & 2 and the test pair are exact.  Every other diagonal
single in the corpus (9 of them) follows the approach-quadrant corner rule, so
that is the canonical transformation encoded here.
"""


def _blocks(g):
    """Return top-left (r, c) of every solid 2x2 block of color 5."""
    H, W = len(g), len(g[0])
    bs = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (g[r][c] == 5 and g[r][c + 1] == 5
                    and g[r + 1][c] == 5 and g[r + 1][c + 1] == 5):
                bs.append((r, c))
    return bs


def _singles(g):
    """Return (r, c, color) for every scattered cell (not background/not 5)."""
    H, W = len(g), len(g[0])
    s = []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v not in (0, 5):
                s.append((r, c, v))
    return s


def _box_man(r, c, br, bc):
    """Manhattan distance from (r, c) to the 2x2 block's bounding box."""
    nr = min(max(r, br), br + 1)
    nc = min(max(c, bc), bc + 1)
    return abs(r - nr) + abs(c - nc)


def _box_cheb(r, c, br, bc):
    """Chebyshev distance from (r, c) to the 2x2 block's bounding box."""
    nr = min(max(r, br), br + 1)
    nc = min(max(c, bc), bc + 1)
    return max(abs(r - nr), abs(c - nc))


def _landing(r, c, br, bc):
    """The frame cell a single at (r, c) snaps onto for block at (br, bc)."""
    row_band = br <= r <= br + 1
    col_band = bc <= c <= bc + 1
    if row_band and not col_band:           # horizontal slide
        return (r, bc - 1 if c < bc else bc + 2)
    if col_band and not row_band:           # vertical slide
        return (br - 1 if r < br else br + 2, c)
    # diagonal: outside corner in the approach quadrant
    tr = br - 1 if r < br else br + 2
    tc = bc - 1 if c < bc else bc + 2
    return (tr, tc)


def infer_T(input_grid):
    """Compute the latent transformation mask as {(r, c): new_color}."""
    g = input_grid
    blocks = _blocks(g)
    singles = _singles(g)
    T = {}
    if not blocks:
        return T

    # Every original single cell is vacated (becomes background).
    for (r, c, _v) in singles:
        T[(r, c)] = 0

    # Place singles closest-to-a-block first so they claim their slot; on a
    # collision the loser falls through to its next nearest block.
    H, W = len(g), len(g[0])
    block_cells = set()
    for (br, bc) in blocks:
        for dr in (0, 1):
            for dc in (0, 1):
                block_cells.add((br + dr, bc + dc))

    occupied = set()
    order = sorted(
        singles,
        key=lambda s: min(_box_man(s[0], s[1], b[0], b[1]) for b in blocks),
    )
    for (r, c, v) in order:
        for (br, bc) in sorted(
            blocks,
            key=lambda b: (_box_man(r, c, b[0], b[1]),
                           _box_cheb(r, c, b[0], b[1]),
                           (r - b[0] - 0.5) ** 2 + (c - b[1] - 0.5) ** 2),
        ):
            cell = _landing(r, c, br, bc)
            if not (0 <= cell[0] < H and 0 <= cell[1] < W):
                continue
            if cell in occupied or cell in block_cells:
                continue
            occupied.add(cell)
            T[cell] = v          # landing cell takes the single's color
            break

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
