"""Canonical solver for ARC puzzle 4e7e0eb9.

Structure of the grid:
  * A non-zero "major separator" color tiles the whole grid into 9x9 blocks
    with single separator lines at indices 9, 19, ... (period 10).
  * Each 9x9 block holds a 2x2 arrangement of 3x3 solid-color tiles. Tiles sit
    at relative rows {1..3, 5..7} and cols {1..3, 5..7}; relative index 4 is the
    inner separator (and the block border indices 0/8 too).

Per-block rule, decided by the block's INNER middle separator (rel row 4 / col 4):
  * inner middle COLUMN is a non-zero marker  -> horizontal mirror
        (swap the left/right tile within each tile-row).
  * inner middle ROW is a non-zero marker     -> vertical mirror
        (swap the top/bottom tile within each tile-column).
  * inner separators are plain (0): the block has three tiles of one color and
        one "odd" tile -> every tile becomes the odd color.

infer_T builds an explicit mask {(r,c): new_color} of only the cells that change;
apply_T copies the input and overwrites just those cells.
"""

from collections import Counter


def _block_ranges(n):
    """Start indices of each 9-cell block (separators are single lines between)."""
    starts = []
    s = 0
    while s < n:
        starts.append(s)
        s += 10
    return starts


def _block_new_tiles(grid, r0, c0):
    """Return the 2x2 dict of NEW tile colors for the block whose top-left is (r0,c0)."""
    def tile_color(tr, tc):
        return grid[r0 + 1 + tr * 4][c0 + 1 + tc * 4]

    tiles = {(tr, tc): tile_color(tr, tc) for tr in range(2) for tc in range(2)}

    # Inner middle separators (rel index 4), sampled inside the tile band.
    mid_row_color = grid[r0 + 4][c0 + 1]  # a cell on the middle row, tile-col band
    mid_col_color = grid[r0 + 1][c0 + 4]  # a cell on the middle col, tile-row band

    new = dict(tiles)
    if mid_col_color != 0:
        # vertical marker line -> horizontal mirror (swap left/right per row)
        for tr in range(2):
            new[(tr, 0)], new[(tr, 1)] = tiles[(tr, 1)], tiles[(tr, 0)]
    elif mid_row_color != 0:
        # horizontal marker line -> vertical mirror (swap top/bottom per col)
        for tc in range(2):
            new[(0, tc)], new[(1, tc)] = tiles[(1, tc)], tiles[(0, tc)]
    else:
        # plain block: three equal tiles + one odd -> all become the odd color
        cnt = Counter(tiles.values())
        if len(cnt) == 2:
            odd = min(cnt, key=cnt.get)
            for k in new:
                new[k] = odd
    return new


def infer_T(input_grid):
    """Build the latent change-mask {(r,c): new_color} from input structure alone."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for r0 in _block_ranges(H):
        for c0 in _block_ranges(W):
            if r0 + 9 > H or c0 + 9 > W:
                continue
            new = _block_new_tiles(input_grid, r0, c0)
            for (tr, tc), color in new.items():
                base_r = r0 + 1 + tr * 4
                base_c = c0 + 1 + tc * 4
                for dr in range(3):
                    for dc in range(3):
                        r, c = base_r + dr, base_c + dc
                        if input_grid[r][c] != color:
                            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
