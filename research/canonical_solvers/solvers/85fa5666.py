"""Canonical latent-T solver for ARC puzzle 85fa5666.

Rule (inferred from input structure alone):
  The grid contains one or more "gadgets": a 2x2 block of color 2, surrounded by
  four single-cell corner markers placed one cell diagonally outside each corner
  of the block (the marker colors come from the set {3,6,7,8}).

  For every gadget the transformation does two things:
    1. The four corner markers are rotated one step clockwise around the block:
         new TL = old BL,  new TR = old TL,  new BR = old TR,  new BL = old BR.
    2. From each corner, a diagonal ray of that corner's NEW color is shot
       outward (away from the block). A ray travels until it reaches the grid
       edge, or until it would step onto another gadget's 2x2 block. As a single
       extra terminator, a ray also stops when it reaches a cell orthogonally
       adjacent to ANOTHER gadget's (post-rotation) corner marker of the SAME
       color as the ray -- i.e. it connects to a like-colored corner -- unless
       the ray is about to reach the grid boundary anyway (edge wins).

  The 2x2 blocks themselves are never modified; only marker corners and the
  diagonal ray cells are overwritten.

infer_T returns the latent mask as a dict {(r,c): new_color}; apply_T copies the
input and overwrites only the masked cells.
"""


def _find_blocks(g):
    """Top-left coordinates of every 2x2 block of color 2."""
    H, W = len(g), len(g[0])
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (g[r][c] == 2 and g[r][c + 1] == 2
                    and g[r + 1][c] == 2 and g[r + 1][c + 1] == 2):
                blocks.append((r, c))
    return blocks


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    def val(r, c):
        return g[r][c] if 0 <= r < H and 0 <= c < W else 0

    blocks = _find_blocks(g)

    # All 2x2 block cells (rays must not overrun a block).
    block_cells = set()
    for (r, c) in blocks:
        for a in (0, 1):
            for b in (0, 1):
                block_cells.add((r + a, c + b))

    # Post-rotation color sitting at each marker-corner position, for all blocks.
    # clockwise rotation: new TL=old BL, new TR=old TL, new BR=old TR, new BL=old BR
    post_corner = {}
    for (r, c) in blocks:
        TL = (r - 1, c - 1); TR = (r - 1, c + 2)
        BL = (r + 2, c - 1); BR = (r + 2, c + 2)
        post_corner[TL] = val(*BL)
        post_corner[TR] = val(*TL)
        post_corner[BR] = val(*TR)
        post_corner[BL] = val(*BR)

    T = {}
    for (r, c) in blocks:
        TL = (r - 1, c - 1); TR = (r - 1, c + 2)
        BL = (r + 2, c - 1); BR = (r + 2, c + 2)
        own_corners = {TL, TR, BL, BR}
        # (corner, new_color, outward diagonal direction)
        rays = [
            (TL, val(*BL), (-1, -1)),
            (TR, val(*TL), (-1, 1)),
            (BR, val(*TR), (1, 1)),
            (BL, val(*BR), (1, -1)),
        ]
        for corner, col, (dr, dc) in rays:
            rr, cc = corner
            while 0 <= rr < H and 0 <= cc < W:
                # never overwrite another gadget's 2x2 block
                if (rr, cc) in block_cells and (rr, cc) != corner:
                    break
                T[(rr, cc)] = col

                # decide whether to terminate after this cell
                nr, nc = rr + dr, cc + dc
                next_on_edge = (
                    not (0 <= nr < H and 0 <= nc < W)
                    or nr in (0, H - 1) or nc in (0, W - 1)
                )
                connects = False
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (rr + a, cc + b)
                    if (nb in post_corner and nb not in own_corners
                            and post_corner[nb] == col):
                        connects = True
                        break
                if connects and not next_on_edge:
                    break
                rr, cc = nr, nc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
