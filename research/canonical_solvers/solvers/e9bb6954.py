"""Canonical solver for ARC puzzle e9bb6954.

Rule (inferred from input structure alone):
- The grid contains one or more solid 3x3 monochromatic blocks (non-zero color).
- Each block projects a full-grid CROSS in its own color: the block's center row
  is painted across the whole width and its center column across the whole height,
  overwriting whatever was there.
- Where one block's center row meets a DIFFERENT block's center column (and vice
  versa) a GAP is left: that intersection cell is cleared to 0.

infer_T builds a latent mask {(r,c): new_color} describing exactly the cells to
overwrite (cross cells -> block color, intersection gaps -> 0). apply_T copies the
input and writes only the masked cells.
"""


def _find_blocks(g):
    """Return list of (color, center_row, center_col) for each solid 3x3 block."""
    H, W = len(g), len(g[0])
    blocks = []
    for r in range(H - 2):
        for c in range(W - 2):
            vals = {g[r + i][c + j] for i in range(3) for j in range(3)}
            if len(vals) == 1 and 0 not in vals:
                color = next(iter(vals))
                blocks.append((color, r + 1, c + 1))
    return blocks


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    blocks = _find_blocks(input_grid)

    # Gap cells: intersection of one block's center row with another block's
    # center column. These get cleared to 0 (applied last so they win over draws).
    gaps = set()
    for i, (_, ri, _) in enumerate(blocks):
        for j, (_, _, clj) in enumerate(blocks):
            if i == j:
                continue
            gaps.add((ri, clj))

    T = {}
    # Paint each block's full-grid cross in its color.
    for color, cr, cc in blocks:
        for c in range(W):
            T[(cr, c)] = color
        for r in range(H):
            T[(r, cc)] = color
    # Apply gaps last.
    for cell in gaps:
        T[cell] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
