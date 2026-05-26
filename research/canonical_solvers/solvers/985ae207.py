"""Canonical solver for ARC puzzle 985ae207.

Rule
----
The grid contains, on a background of 8:
  * a number of 3x3 "stamp" boxes: a uniform-colored 3x3 ring with a single
    differently-colored center cell, and
  * large solid rectangles (area > 9) of various colors.

Each stamp box has a center color C; there is exactly one large rectangle whose
color equals C (its target).  The box and its target are aligned on a common
band (their row ranges overlap -> horizontal motion; otherwise their column
ranges overlap -> vertical motion).  The 3x3 stamp is then replicated edge to
edge (pitch 3) from the box toward the target, the chain of stamp centers
stepping by 3 each time until the last center lands exactly on the target's
near edge.  Each replicated stamp is drawn (frame + center) over the grid,
overwriting whatever was underneath.

The latent transformation T is the mask of all cells painted by these
replicated stamps; apply_T copies the input and overwrites only those cells.
"""


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or grid[rr][cc] != col:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                rs = [p[0] for p in cells]
                cs = [p[1] for p in cells]
                comps.append({
                    "color": col,
                    "r0": min(rs), "r1": max(rs),
                    "c0": min(cs), "c1": max(cs),
                    "size": len(cells),
                    "cells": set(cells),
                })
    return comps


def _find_boxes(grid, bg):
    """Find all 3x3 ring boxes -> (top, left, frame_color, center_color)."""
    H, W = len(grid), len(grid[0])
    boxes = []
    for r in range(H - 2):
        for c in range(W - 2):
            ring = [
                grid[r][c], grid[r][c + 1], grid[r][c + 2],
                grid[r + 1][c], grid[r + 1][c + 2],
                grid[r + 2][c], grid[r + 2][c + 1], grid[r + 2][c + 2],
            ]
            ctr = grid[r + 1][c + 1]
            if len(set(ring)) == 1 and ring[0] != bg and ring[0] != ctr:
                boxes.append((r, c, ring[0], ctr))
    return boxes


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # background = most frequent color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    boxes = _find_boxes(input_grid, bg)
    comps = _components(input_grid, bg)
    # target rectangles: solid blocks with area > 9 (bigger than a 3x3 box)
    big = [cc for cc in comps
           if (cc["r1"] - cc["r0"] + 1) * (cc["c1"] - cc["c0"] + 1) > 9]

    T = {}  # (r, c) -> color

    for (br, bc, frame, center) in boxes:
        # pattern of this stamp: frame on the ring, center in the middle
        cr, cc0 = br + 1, bc + 1  # box center

        targets = [t for t in big if t["color"] == center]
        if not targets:
            continue
        tgt = targets[0]

        # decide motion axis: do row bands overlap?
        row_overlap = not (br + 2 < tgt["r0"] or br > tgt["r1"])
        col_overlap = not (bc + 2 < tgt["c0"] or bc > tgt["c1"])

        centers = []
        if row_overlap and not col_overlap:
            # horizontal motion
            if tgt["c0"] > cc0:         # target to the right
                near = tgt["c0"]        # last stamp center lands on near edge column
                if (near - cc0) % 3 != 0:
                    continue
                col = cc0
                while col <= near:
                    centers.append((cr, col))
                    col += 3
            else:                       # target to the left
                near = tgt["c1"]
                if (cc0 - near) % 3 != 0:
                    continue
                col = cc0
                while col >= near:
                    centers.append((cr, col))
                    col -= 3
        elif col_overlap and not row_overlap:
            # vertical motion
            if tgt["r0"] > cr:          # target below
                near = tgt["r0"]
                if (near - cr) % 3 != 0:
                    continue
                row = cr
                while row <= near:
                    centers.append((row, cc0))
                    row += 3
            else:                       # target above
                near = tgt["r1"]
                if (cr - near) % 3 != 0:
                    continue
                row = cr
                while row >= near:
                    centers.append((row, cc0))
                    row -= 3
        else:
            continue

        # draw a stamp (3x3 ring + center) at every chosen center
        for (sr, sc) in centers:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, ccc = sr + dr, sc + dc
                    if 0 <= rr < H and 0 <= ccc < W:
                        T[(rr, ccc)] = center if (dr == 0 and dc == 0) else frame

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
