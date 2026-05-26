"""Canonical solver for ARC puzzle 7e0986d6.

Rule (denoise rectangular blocks, erase scattered specks):
  The grid has a background color, a dominant "fill" color that forms solid
  rectangular blocks, and a third "noise" color. Noise cells appear both
  INSIDE the rectangular blocks (as holes punched into the fill) and OUTSIDE
  them as isolated single-cell specks on the background.

  Transformation: only noise cells change.
    - A noise cell that lies inside a rectangular block -> repaint to fill.
    - A noise cell that is an isolated background speck   -> erase to background.
  Fill cells and background cells never change.

  Blocks are recovered by greedily extracting the largest solid (all
  non-background) rectangle, marking and consuming its cells, and repeating.
  This correctly splits rectangles that touch edge-to-edge: the bigger one is
  taken first, then the smaller. Isolated background specks can never form a
  rectangle of area >= 2 (they are never orthogonally adjacent), so they are
  never marked as block and get erased.

  T is the latent mask {(r, c): new_color} of noise cells to overwrite.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Color roles from frequency.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    nonbg = {k: v for k, v in counts.items() if k != bg}
    if not nonbg:
        return {}
    fill = max(nonbg, key=nonbg.get)
    others = [k for k in nonbg if k != fill]
    noise = others[0] if others else None

    # Recover rectangular blocks: greedily take the largest all-non-bg
    # rectangle, mark/consume it, repeat. Anything left is background noise.
    avail = [[input_grid[r][c] != bg for c in range(W)] for r in range(H)]
    block = [[False] * W for _ in range(H)]

    while True:
        best = None  # (area, r1, c1, r2, c2)
        for r1 in range(H):
            for c1 in range(W):
                if not avail[r1][c1]:
                    continue
                maxc = W - 1
                for r2 in range(r1, H):
                    # Largest c2 such that rows r1..r2, cols c1..c2 are all available.
                    cc = c1
                    while cc <= maxc and avail[r2][cc]:
                        cc += 1
                    maxc = min(maxc, cc - 1)
                    if maxc < c1:
                        break
                    for c2 in range(c1, maxc + 1):
                        area = (r2 - r1 + 1) * (c2 - c1 + 1)
                        if best is None or area > best[0]:
                            best = (area, r1, c1, r2, c2)
        if best is None or best[0] < 2:
            break
        _, r1, c1, r2, c2 = best
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                block[rr][cc] = True
                avail[rr][cc] = False

    # Latent mask: only noise cells are overwritten.
    T = {}
    if noise is not None:
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] == noise:
                    T[(r, c)] = fill if block[r][c] else bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
