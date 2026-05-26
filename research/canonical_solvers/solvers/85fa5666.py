"""Canonical solver for ARC puzzle 85fa5666.

Rule
----
The grid contains one or more 2x2 blocks of colour 2.  Each block is
surrounded by four single-cell "corner markers" sitting just outside its
diagonal corners (one cell up-left, up-right, down-left, down-right of the
2x2).  The transformation:

  1. Rotate the four corner markers one quarter-turn clockwise: each corner
     position takes the colour of its counter-clockwise neighbour
     (TL<-BL, TR<-TL, BR<-TR, BL<-BR).

  2. From every (rotated) corner marker draw a diagonal ray outward, away
     from the block, using the marker's new colour.  The ray fills
     background cells until it leaves the grid or meets a non-background
     cell.

  3. A ray that is rounding the corner of *another* block is blocked: when
     the next diagonal step is pinched between two occupied cells (the
     other block's 2x2 cell and one of its corner markers) and that marker
     has the same colour as the ray, the ray stops -- unless there is no
     room to penetrate further (the step is at the grid border), in which
     case the terminal cell is still drawn.

Everything is expressed as a latent mask T (dict {(r,c): colour}) computed
from the input alone; apply_T overlays it on a copy of the input.
"""


def _find_blocks(grid):
    """Top-left coordinates of every 2x2 block of colour 2."""
    H, W = len(grid), len(grid[0])
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (grid[r][c] == 2 and grid[r][c + 1] == 2 and
                    grid[r + 1][c] == 2 and grid[r + 1][c + 1] == 2):
                blocks.append((r, c))
    return blocks


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    def occ(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] != 0

    # corner order is clockwise: TL, TR, BR, BL ; outward diagonal per corner
    dirs = [(-1, -1), (-1, 1), (1, 1), (1, -1)]

    # gather corner markers / their rotated (new) colours for every block
    new_color = {}          # marker position -> rotated colour
    block_corners = []      # list of (corners, new_colors)
    for (tr, lc) in _find_blocks(input_grid):
        br, rc = tr + 1, lc + 1
        corners = [(tr - 1, lc - 1), (tr - 1, rc + 1),
                   (br + 1, rc + 1), (br + 1, lc - 1)]
        old = [input_grid[r][c] if 0 <= r < H and 0 <= c < W else 0
               for (r, c) in corners]
        new = [old[(i - 1) % 4] for i in range(4)]   # clockwise rotation
        for pos, col in zip(corners, new):
            new_color[pos] = col
        block_corners.append((corners, new))

    T = {}
    for corners, new in block_corners:
        for i, (cr, cc) in enumerate(corners):
            if not (0 <= cr < H and 0 <= cc < W):
                continue
            color = new[i]
            T[(cr, cc)] = color                       # recoloured marker
            dr, dc = dirs[i]
            rr, cc2 = cr, cc
            while True:
                nr, nc = rr + dr, cc2 + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    break
                if input_grid[nr][nc] != 0:
                    break
                # diagonal pinch by another block's same-colour corner
                f1 = (rr, cc2 + dc)
                f2 = (rr + dr, cc2)
                if (occ(*f1) and occ(*f2) and
                        (new_color.get(f1) == color or
                         new_color.get(f2) == color)):
                    beyond = (nr + dr, nc + dc)
                    if 0 <= beyond[0] < H and 0 <= beyond[1] < W:
                        break
                T[(nr, nc)] = color
                rr, cc2 = nr, nc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
