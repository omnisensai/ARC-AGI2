"""Canonical solver for ARC puzzle 52df9849.

Rule (same-size):
The grid contains a background color plus several colored objects. Some objects
are regular shapes (filled rectangles / bars, or straight diagonal lines) that
are partially occluded by another object: where they cross the occluder, the
occluder's color is shown instead of theirs. The transformation completes each
such occluded regular shape, redrawing it in full on top of whatever occludes
it. Unoccluded complete shapes and irregular blobs are left untouched.

Detection of a "completable" object:
  - filled rectangle: every cell of its bounding box is non-background (i.e. it
    is itself or another object) -> redraw the whole bounding box in its color.
  - straight diagonal line: all its cells share r-c or r+c -> redraw the full
    diagonal segment between its extreme cells in its color.
Objects whose bounding box contains background cells and that are not diagonals
(blobs) are skipped.

infer_T builds the latent mask (dict {(r,c): new_color}); apply_T overwrites
only the masked cells.
"""

from collections import Counter


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return max(cnt, key=cnt.get)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)

    # collect cells per non-background color
    cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                cells.setdefault(v, []).append((r, c))

    T = {}                      # latent mask: (r,c) -> new color
    rect_fills = []             # (color, list_of_cells)
    diag_fills = []             # (color, list_of_cells)

    for color, pts in cells.items():
        pset = set(pts)
        rs = [r for r, _ in pts]
        cs = [c for _, c in pts]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # is the bounding box completely non-background (a filled rectangle)?
        bg_inside = False
        other_inside = False
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) in pset:
                    continue
                if input_grid[r][c] == bg:
                    bg_inside = True
                else:
                    other_inside = True

        if not bg_inside:
            # true filled rectangle; only redraw if it is occluded
            if other_inside:
                bbox_cells = [(r, c) for r in range(r0, r1 + 1)
                              for c in range(c0, c1 + 1)]
                rect_fills.append((color, bbox_cells))
            continue

        # not a filled rectangle: check for a straight diagonal line
        diffs = set(r - c for r, c in pts)
        sums = set(r + c for r, c in pts)
        if len(diffs) == 1:
            # cells lie on r - c = k ; fill from min to max row
            k = diffs.pop()
            seg = [(r, r - k) for r in range(r0, r1 + 1)]
            if all(0 <= c < W for _, c in seg):
                diag_fills.append((color, seg))
        elif len(sums) == 1:
            k = sums.pop()
            seg = [(r, k - r) for r in range(r0, r1 + 1)]
            if all(0 <= c < W for _, c in seg):
                diag_fills.append((color, seg))
        # otherwise it is an irregular blob: leave untouched

    # rectangles first, then diagonals drawn on top
    for color, cell_list in rect_fills:
        for (r, c) in cell_list:
            T[(r, c)] = color
    for color, cell_list in diag_fills:
        for (r, c) in cell_list:
            T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
