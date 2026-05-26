"""Canonical latent-T solver for ARC puzzle 195c6913.

Rule (inferred from ALL pairs):
  The grid is split into two background regions by a meandering 45-degree
  "river" boundary.  In the top-left corner sits a "legend": a row of 2x2
  colour blocks that, read left-to-right, define a periodic colour sequence.
  An isolated 2x2 block elsewhere defines the "terminator" colour.  Single
  non-background cells on the border are "markers".

  Each marker emits a ray that travels straight into the region of its inward
  neighbour, painting the periodic legend sequence cell-by-cell (continuously
  across corners).  When the ray reaches the river bank (the other region) it
  drops the terminator colour onto that bank cell and reflects like light off a
  "/" diagonal mirror (right<->up, left<->down), continuing to paint the same
  running sequence.  The ray stops when it would leave the grid or cannot
  reflect.  Finally the legend blocks and the terminator block are erased back
  to their local background colour.

  infer_T builds the latent mask (a {(r, c): new_color} dict of erasures + ray
  paint); apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _find_blocks(inp, bg2):
    """Find all isolated 2x2 monochromatic non-background blocks."""
    H, W = len(inp), len(inp[0])
    blocks, seen = [], set()
    for r in range(H - 1):
        for c in range(W - 1):
            v = inp[r][c]
            if v in bg2 or (r, c) in seen:
                continue
            if inp[r][c + 1] == v and inp[r + 1][c] == v and inp[r + 1][c + 1] == v:
                blocks.append((r, c, v))
                for dr in (0, 1):
                    for dc in (0, 1):
                        seen.add((r + dr, c + dc))
    return blocks


def infer_T(input_grid):
    inp = input_grid
    H, W = len(inp), len(inp[0])

    # The two background colours are simply the two most common colours.
    common = Counter(v for row in inp for v in row).most_common()
    bg2 = [common[0][0], common[1][0]]

    blocks = _find_blocks(inp, bg2)
    # Legend = 2x2 blocks near the top edge, read left-to-right -> sequence.
    legend = sorted([b for b in blocks if b[0] <= 2], key=lambda b: b[1])
    seq = [b[2] for b in legend]
    # Terminator block = the other isolated 2x2 block.
    target = [b for b in blocks if b[0] > 2]
    term = target[0][2] if target else None

    block_cells = set()
    for r, c, _ in blocks:
        for dr in (0, 1):
            for dc in (0, 1):
                block_cells.add((r + dr, c + dc))

    # Markers = single non-background cells that are not part of any 2x2 block.
    markers = []
    for r in range(H):
        for c in range(W):
            if inp[r][c] not in bg2 and (r, c) not in block_cells:
                markers.append((r, c))

    def in_region(rr, cc, region):
        return 0 <= rr < H and 0 <= cc < W and inp[rr][cc] == region

    T = {}  # latent mask: cell -> new colour

    # 1) Erase every 2x2 block (legend + terminator) to its local background.
    for r, c, _ in blocks:
        bg_local = None
        for ar, ac in ((r - 1, c), (r + 2, c), (r, c - 1), (r, c + 2),
                       (r - 1, c - 1), (r + 2, c + 2)):
            if 0 <= ar < H and 0 <= ac < W and inp[ar][ac] in bg2:
                bg_local = inp[ar][ac]
                break
        if bg_local is None:
            bg_local = bg2[0]
        for dr in (0, 1):
            for dc in (0, 1):
                T[(r + dr, c + dc)] = bg_local

    # 2) Trace each marker's ray, reflecting off the river ("/" mirror).
    if seq and term is not None:
        for mr, mc in markers:
            if mc == 0:
                dr, dc = 0, 1
            elif mc == W - 1:
                dr, dc = 0, -1
            elif mr == 0:
                dr, dc = 1, 0
            else:
                dr, dc = -1, 0
            # Ray lives in the region of the marker's inward neighbour.
            if 0 <= mr + dr < H and 0 <= mc + dc < W:
                region = inp[mr + dr][mc + dc]
            else:
                region = bg2[1]

            r, c, idx = mr, mc, 0
            painted = {}
            for _ in range(H * W * 4):
                if (r, c) not in painted:
                    painted[(r, c)] = seq[idx % len(seq)]
                nr, nc = r + dr, c + dc
                if in_region(nr, nc, region):
                    r, c, idx = nr, nc, idx + 1
                    continue
                if not (0 <= nr < H and 0 <= nc < W):
                    break  # ray exits the grid
                # Hit the river bank: drop terminator, reflect off "/" mirror.
                painted[(nr, nc)] = term
                ndr, ndc = -dc, -dr
                if not in_region(r + ndr, c + ndc, region):
                    break  # cannot reflect -> ray ends
                dr, dc = ndr, ndc
                r, c, idx = r + dr, c + dc, idx + 1

            for cell, colour in painted.items():
                T[cell] = colour

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if v is not None:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
