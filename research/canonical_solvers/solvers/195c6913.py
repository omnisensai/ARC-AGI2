"""Canonical solver for ARC puzzle 195c6913.

Rule (same-size):
  The grid is split into two large regions whose shared boundary is a diagonal
  "coastline" staircase.  A horizontal row of 2x2 blocks at the top is a LEGEND
  that defines a repeating colour sequence S (blocks read left-to-right).  A
  single 2x2 block elsewhere defines the ENDPOINT cap colour.  On the left edge
  (column 0) there are single-cell MARKERS, each coloured S[0]; every marker
  seeds a "snake".

  Each snake enters its region moving Right and walks straight while the cell
  ahead stays in that region.  When the cell ahead is the OTHER region it drops
  an endpoint cap there and turns 90 degrees (Right->Up, Up->Right); if the turn
  target is not in the region, or the cell ahead is the grid edge, it stops.
  Cells along the walk are painted with S cycled continuously (the marker cell
  is index 0 == S[0]).

  infer_T builds the mask of all cells to overwrite (snake cells + caps + the
  erased legend/endpoint blocks); apply_T copies the input and overwrites only
  those cells.
"""
from collections import Counter


def _find_blocks(g, H, W, bigset):
    """Find solid 2x2 single-colour blocks of a minority colour."""
    blocks = []
    used = set()
    for r in range(H - 1):
        for c in range(W - 1):
            v = g[r][c]
            if v in bigset or (r, c) in used:
                continue
            if g[r][c + 1] == v and g[r + 1][c] == v and g[r + 1][c + 1] == v:
                blocks.append((r, c, v))
                for dr in (0, 1):
                    for dc in (0, 1):
                        used.add((r + dr, c + dc))
    return blocks


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    cnt = Counter()
    for row in g:
        for v in row:
            cnt[v] += 1
    common = [c for c, _ in cnt.most_common()]
    bigset = set(common[:2])  # the two large regions

    # legend (top row of 2x2 blocks) + endpoint block
    blocks = _find_blocks(g, H, W, bigset)
    minr = min(b[0] for b in blocks)
    legend = sorted((b for b in blocks if b[0] == minr), key=lambda b: b[1])
    seq = [b[2] for b in legend]            # repeating colour sequence
    L = len(seq)
    endcolor = next(b[2] for b in blocks if b[0] > minr + 1)

    # latent transformation mask: {(r, c): new_colour}
    T = {}

    # 1) erase legend + endpoint blocks back to the surrounding big region
    for (br, bc, _v) in blocks:
        fill = None
        for dr in range(-1, 3):
            for dc in range(-1, 3):
                rr, cc = br + dr, bc + dc
                if 0 <= rr < H and 0 <= cc < W and g[rr][cc] in bigset:
                    fill = g[rr][cc]
                    break
            if fill is not None:
                break
        for dr in (0, 1):
            for dc in (0, 1):
                T[(br + dr, bc + dc)] = fill

    # 2) trace each snake from its left-edge marker
    markers = [r for r in range(H) if g[r][0] not in bigset]
    for mr in markers:
        river = g[mr][1]                    # region this marker enters
        r, c = mr, 0
        d = (0, 1)                          # start moving Right
        idx = 0                             # marker cell == index 0 == seq[0]
        T[(mr, 0)] = seq[0]
        while True:
            nr, nc = r + d[0], c + d[1]
            inb = 0 <= nr < H and 0 <= nc < W
            if inb and g[nr][nc] == river:
                r, c = nr, nc
                idx += 1
                T[(r, c)] = seq[idx % L]
            else:
                if not inb:
                    break                   # grid edge -> stop
                # blocked by the other region: drop cap, then turn
                T[(nr, nc)] = endcolor
                if d == (0, 1):
                    nd = (-1, 0)            # Right -> Up
                elif d == (-1, 0):
                    nd = (0, 1)            # Up -> Right
                else:
                    break
                tr, tc = r + nd[0], c + nd[1]
                if 0 <= tr < H and 0 <= tc < W and g[tr][tc] == river:
                    d = nd
                else:
                    break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
