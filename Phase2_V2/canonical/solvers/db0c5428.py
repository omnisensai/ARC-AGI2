"""Canonical solver for ARC puzzle db0c5428.

Structure: a single 9x9 block sits on a background. The block is a 3x3
arrangement of 3x3 sub-cells; its centre sub-cell is a hole filled with the
global background colour. The transformation:
  * fills the central hole with the ring of cells that touch it (the cells at
    block offsets 2/4/6 along each axis), with the very centre set to the
    block's own dominant colour;
  * projects each of the 8 perimeter sub-cells outward (rotated 180 degrees)
    into the background, in the direction it faces relative to the block.
Only background cells are overwritten.
"""


def _dominant(grid):
    cnt = {}
    for row in grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    return max(cnt, key=cnt.get)


def _block_bounds(grid, bg):
    H, W = len(grid), len(grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] != bg]
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _rot180_3x3(block, r0, c0):
    # 3x3 sub-cell at (r0,c0), rotated 180 degrees, returned as 3x3 list.
    return [[block[r0 + (2 - i)][c0 + (2 - j)] for j in range(3)] for i in range(3)]


def infer_T(input_grid):
    """Return latent mask {(r,c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _dominant(input_grid)
    r0, r1, c0, c1 = _block_bounds(input_grid, bg)
    bh, bw = r1 - r0 + 1, c1 - c0 + 1

    T = {}
    # Only handle the expected 9x9 (3x3 of 3x3) block with a 3x3 centre hole.
    if bh != 9 or bw != 9:
        return T

    # Dominant colour inside the block (its local background).
    bcnt = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = input_grid[r][c]
            if v != bg:
                bcnt[v] = bcnt.get(v, 0) + 1
    block_bg = max(bcnt, key=bcnt.get) if bcnt else bg

    # 1) Fill the central hole (block sub-cell [1][1], i.e. block rows 3-5,
    #    cols 3-5 -> grid rows r0+3..r0+5, cols c0+3..c0+5).
    feed = (2, 4, 6)
    for i in range(3):
        for j in range(3):
            tr, tc = r0 + 3 + i, c0 + 3 + j
            if i == 1 and j == 1:
                T[(tr, tc)] = block_bg
            else:
                T[(tr, tc)] = input_grid[r0 + feed[i]][c0 + feed[j]]

    # 2) Project the 8 perimeter sub-cells outward (rotated 180).
    for br in range(3):
        for bc in range(3):
            if br == 1 and bc == 1:
                continue
            src = _rot180_3x3(input_grid, r0 + br * 3, c0 + bc * 3)
            # Destination top-left in the grid.
            dr = r0 - 3 if br == 0 else (r1 + 1 if br == 2 else r0 + br * 3)
            dc = c0 - 3 if bc == 0 else (c1 + 1 if bc == 2 else c0 + bc * 3)
            for i in range(3):
                for j in range(3):
                    rr, cc = dr + i, dc + j
                    if 0 <= rr < H and 0 <= cc < W:
                        T[(rr, cc)] = src[i][j]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
