"""Canonical solver for ARC puzzle ac3e2b04.

Structure of the puzzle:
  * The grid contains several full-length lines of color 2, all running in a
    single orientation (all horizontal rows, or all vertical columns). Boxes
    overlaying a line can interrupt it, so a line is detected as a row/column
    that is *mostly* color 2.
  * One or more 3x3 "boxes" sit ON these 2-lines: a ring of color 3 around a
    center cell of color 2. Each box marks a position *along* its line, i.e. a
    perpendicular coordinate.

Transformation:
  * For every box, draw a full-grid line of color 1 perpendicular to the
    2-lines, passing through the box's perpendicular coordinate (a "cross-line").
  * Wherever a cross-line meets a 2-line, stamp a 3x3 ring of color 1 around
    that intersection (a "1-box"), keeping the 2 at the intersection center.
  * The original 3-boxes are left untouched (their 3-ring is restored).

infer_T computes the latent overwrite mask {(r,c): color}; apply_T copies the
input and overwrites only those cells.
"""


def _find_lines_and_boxes(g):
    H, W = len(g), len(g[0])
    rows2 = [r for r in range(H)
             if sum(1 for c in range(W) if g[r][c] == 2) >= W // 2]
    cols2 = [c for c in range(W)
             if sum(1 for r in range(H) if g[r][c] == 2) >= H // 2]
    centers = [(r, c)
               for r in range(1, H - 1) for c in range(1, W - 1)
               if g[r][c] == 2 and all(
                   g[r + dr][c + dc] == 3
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                   if (dr, dc) != (0, 0))]
    return rows2, cols2, centers


def infer_T(g):
    """Return latent mask dict {(r,c): new_color}."""
    H, W = len(g), len(g[0])
    rows2, cols2, centers = _find_lines_and_boxes(g)
    horizontal = len(rows2) > 0  # 2-lines run horizontally (rows)
    lines = rows2 if horizontal else cols2
    T = {}

    if horizontal:
        cross_cols = sorted(set(c for _, c in centers))
        # vertical cross-lines of color 1 spanning full height
        for cc in cross_cols:
            for r in range(H):
                T[(r, cc)] = 1
        # 1-box rings at every (line-row, cross-col) intersection
        for lr in lines:
            for cc in cross_cols:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, ccc = lr + dr, cc + dc
                        if 0 <= rr < H and 0 <= ccc < W:
                            T[(rr, ccc)] = 2 if (dr, dc) == (0, 0) else 1
    else:
        cross_rows = sorted(set(r for r, _ in centers))
        for cr in cross_rows:
            for c in range(W):
                T[(cr, c)] = 1
        for lc in lines:
            for cr in cross_rows:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = cr + dr, lc + dc
                        if 0 <= rr < H and 0 <= cc < W:
                            T[(rr, cc)] = 2 if (dr, dc) == (0, 0) else 1

    # restore the original 3-boxes (they are never overwritten)
    for (cr, cc) in centers:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, ccc = cr + dr, cc + dc
                if 0 <= rr < H and 0 <= ccc < W:
                    T[(rr, ccc)] = 2 if (dr, dc) == (0, 0) else 3
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
