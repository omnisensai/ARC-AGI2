"""Canonical solver for ARC puzzle b7f8a4d8.

Structure: a regular lattice of square "cells", each a frame color enclosing an
interior color, separated by background (0) gaps. Most cells share one common
("background") interior color; a few cells have a special interior color. For
each special color, the cells carrying it occur at the four corners of one or
more axis-aligned rectangles in the lattice. The transformation draws each such
rectangle's perimeter through the gap (0) cells between the corner cells,
restricted to the interior row/column band of the cells, painting it with the
special color.

Latent T: dict {(r, c): color} of gap cells to overwrite.
"""

from collections import Counter
from itertools import combinations


def _detect_blocks(g):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if a < 0 or a >= H or b < 0 or b >= W:
                        continue
                    if seen[a][b] or g[a][b] == 0:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    # Parse each frame+interior cell; skip edge-clipped frame-only fragments.
    raw = []
    for cells in _detect_blocks(input_grid):
        rs = [a for a, b in cells]
        cs = [b for a, b in cells]
        r0, c0 = min(rs), min(cs)
        frame = input_grid[r0][c0]
        int_cells = [(a, b) for (a, b) in cells if input_grid[a][b] != frame]
        if not int_cells:
            continue  # purely a clipped frame, has no interior -> not a real cell
        interior = input_grid[int_cells[0][0]][int_cells[0][1]]
        irows = sorted({a for a, b in int_cells})
        icols = sorted({b for a, b in int_cells})
        raw.append((r0, c0, interior, irows, icols))

    if not raw:
        return {}

    # Map pixel-space cell origins to lattice (row, col) indices.
    r0s = sorted({b[0] for b in raw})
    c0s = sorted({b[1] for b in raw})
    rmap = {r: i for i, r in enumerate(r0s)}
    cmap = {c: i for i, c in enumerate(c0s)}

    bg = Counter(b[2] for b in raw).most_common(1)[0][0]

    cellinfo = {}  # (lr, lc) -> (interior, irows, icols)
    for (r0, c0, interior, irows, icols) in raw:
        cellinfo[(rmap[r0], cmap[c0])] = (interior, irows, icols)

    # Group special (non-background) cells by their interior color.
    spec = {}
    for (lr, lc), (interior, irows, icols) in cellinfo.items():
        if interior != bg:
            spec.setdefault(interior, []).append((lr, lc))

    T = {}
    for color, cells in spec.items():
        cset = set(cells)
        rows = sorted({r for r, c in cells})
        cols = sorted({c for r, c in cells})
        # Every axis-aligned rectangle whose four lattice corners carry this color.
        for r1l, r2l in combinations(rows, 2):
            for c1l, c2l in combinations(cols, 2):
                if not all((rr, cc) in cset
                           for rr in (r1l, r2l) for cc in (c1l, c2l)):
                    continue
                # Horizontal edges (lattice rows r1l, r2l) across the gap columns.
                for lr in (r1l, r2l):
                    _, irows, icols_left = cellinfo[(lr, c1l)]
                    _, _, icols_right = cellinfo[(lr, c2l)]
                    cstart = max(icols_left) + 1
                    cend = min(icols_right) - 1
                    for rr in irows:
                        for cc in range(cstart, cend + 1):
                            if input_grid[rr][cc] == 0:
                                T[(rr, cc)] = color
                # Vertical edges (lattice cols c1l, c2l) down the gap rows.
                for lc in (c1l, c2l):
                    _, irows_top, icols = cellinfo[(r1l, lc)]
                    _, irows_bot, _ = cellinfo[(r2l, lc)]
                    rstart = max(irows_top) + 1
                    rend = min(irows_bot) - 1
                    for cc in icols:
                        for rr in range(rstart, rend + 1):
                            if input_grid[rr][cc] == 0:
                                T[(rr, cc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
