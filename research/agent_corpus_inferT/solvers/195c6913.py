"""Canonical latent-T solver for ARC puzzle 195c6913.

Structure of every pair:
  * Two dominant colours fill the grid: a WALL colour and a CORRIDOR colour.
    The corridor is a winding diagonal band; the wall is everything else.
  * A row of 2x2 "palette" blocks (rare colours) sits near the top, embedded
    in the wall.  Read left-to-right they give a repeating colour sequence.
  * One extra lone 2x2 block of a rare colour is the CAP/key colour.
  * One or two single rare cells on the left edge (colour == palette[0]) are
    SNAKE markers / entry points.

Transformation (the latent mask T):
  Erase every rare 2x2 block back to the wall colour.  From each left-edge
  marker run a "snake": it enters moving right and travels through the corridor
  painting the repeating palette sequence cell by cell.  When the cell ahead is
  a wall it drops the cap colour there and turns 90 degrees, keeping a fixed
  diagonal sense (it always zig-zags toward the same diagonal corner).  It
  stops at the grid edge.  The fixed diagonal row-direction is the one that
  maximises total snake length over all markers.

infer_T builds the {(r,c): colour} mask from the input alone; apply_T copies
the input and overwrites only the masked cells.
"""

from collections import Counter


def _analyze(inp):
    H = len(inp); W = len(inp[0])
    ci = Counter(v for row in inp for v in row)
    dominant = [c for c, _ in ci.most_common(2)]  # wall + corridor colours

    # rare 2x2 blocks (palette blocks + the lone cap block)
    blocks = []; seen = set()
    for r in range(H - 1):
        for c in range(W - 1):
            if (r, c) in seen:
                continue
            v = inp[r][c]
            if v in dominant:
                continue
            if inp[r][c + 1] == v and inp[r + 1][c] == v and inp[r + 1][c + 1] == v:
                blocks.append((r, c, v))
                for dr in (0, 1):
                    for dc in (0, 1):
                        seen.add((r + dr, c + dc))

    # palette = the row of blocks that shares the most common block-row
    rowcount = Counter(b[0] for b in blocks)
    palrow = rowcount.most_common(1)[0][0]
    pal = sorted([b for b in blocks if b[0] == palrow], key=lambda b: b[1])
    lone = [b for b in blocks if b[0] != palrow]
    palseq = [b[2] for b in pal]
    cap = lone[0][2]

    # wall = colour immediately left of the first palette block; corridor = the
    # other dominant colour.
    pr, pc, _ = pal[0]
    wall = inp[pr][pc - 1]
    corridor = max((c for c in dominant if c != wall), key=lambda c: ci[c])

    # markers: rare single cells on the left edge (not part of any block)
    markers = [(r, 0) for r in range(H)
               if inp[r][0] not in dominant and (r, 0) not in seen]

    return dict(H=H, W=W, wall=wall, corridor=corridor, palseq=palseq,
                cap=cap, blocks=blocks, markers=markers)


def _trial_len(inp, r, c, corridor, rowsign):
    """Length of the snake from (r,c) under a given fixed diagonal row sign."""
    H = len(inp); W = len(inp[0])
    dr, dc = 0, 1
    visited = {(r, c)}
    n = 1; steps = 0
    while steps < H * W * 4:
        steps += 1
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W and inp[nr][nc] == corridor and (nr, nc) not in visited:
            r, c = nr, nc; visited.add((r, c)); n += 1; continue
        if not (0 <= nr < H and 0 <= nc < W):
            break
        ndr, ndc = (rowsign, 0) if dr == 0 else (0, 1)
        tr, tc = r + ndr, c + ndc
        if not (0 <= tr < H and 0 <= tc < W and inp[tr][tc] == corridor and (tr, tc) not in visited):
            break
        dr, dc = ndr, ndc
    return n


def _run_snake(inp, T, r, c, corridor, palseq, cap, rowsign):
    """Record the snake's painted cells (and caps) into the mask T."""
    H = len(inp); W = len(inp[0])
    L = len(palseq)
    idx = 0
    T[(r, c)] = palseq[idx]            # marker cell -> first palette colour
    dr, dc = 0, 1                      # enters from left edge moving right
    visited = {(r, c)}
    steps = 0
    while steps < H * W * 4:
        steps += 1
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W and inp[nr][nc] == corridor and (nr, nc) not in visited:
            r, c = nr, nc; idx += 1; visited.add((r, c))
            T[(r, c)] = palseq[idx % L]
            continue
        if not (0 <= nr < H and 0 <= nc < W):
            break                       # reached the grid edge: snake ends
        if inp[nr][nc] != corridor:
            T[(nr, nc)] = cap           # drop cap on the wall, then turn
        ndr, ndc = (rowsign, 0) if dr == 0 else (0, 1)
        tr, tc = r + ndr, c + ndc
        if not (0 <= tr < H and 0 <= tc < W and inp[tr][tc] == corridor and (tr, tc) not in visited):
            break
        dr, dc = ndr, ndc


def infer_T(input_grid):
    """Infer the transformation mask T: {(r, c): colour} of cells to overwrite."""
    info = _analyze(input_grid)
    corridor = info['corridor']; wall = info['wall']
    palseq = info['palseq']; cap = info['cap']
    T = {}
    # erase every rare 2x2 block back to the wall colour
    for (r, c, _) in info['blocks']:
        for dr in (0, 1):
            for dc in (0, 1):
                T[(r + dr, c + dc)] = wall
    # choose the global diagonal row sign (max total snake length)
    best, bestlen = -1, -1
    for rs in (-1, 1):
        tot = sum(_trial_len(input_grid, mr, mc, corridor, rs)
                  for (mr, mc) in info['markers'])
        if tot > bestlen:
            bestlen, best = tot, rs
    # run each snake, overwriting the erased blocks where they overlap
    for (mr, mc) in info['markers']:
        _run_snake(input_grid, T, mr, mc, corridor, palseq, cap, best)
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the mask T."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
