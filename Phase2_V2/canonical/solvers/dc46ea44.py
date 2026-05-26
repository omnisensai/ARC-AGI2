"""Canonical solver for ARC task dc46ea44.

Structure of every input:
  * A horizontal divider line of a single color spans the full width.
  * Below the divider sit two objects on the background:
      - a "6" arrow: a vertical bar (3 cells) plus a diagonal tip; the arrow
        points toward the top-left.
      - another colored object of arbitrary shape.

Transformation:
  * Clear the region below the divider.
  * Translate the arrow straight up so the top of its vertical bar reaches the
    top edge of the grid (row 0).
  * Translate the other object (keeping its exact shape) so that the
    bottom-right corner of its bounding box lands on the upper cell of the
    arrow's (now shifted) diagonal tip.

The latent transformation T is the set of cells whose color changes, with the
new color for each; apply_T copies the input and overwrites only those cells.
"""

from collections import Counter, defaultdict


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color overall.
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]

    # Find the full-width horizontal divider line.
    line_row, line_color = None, None
    for r in range(H):
        vals = set(input_grid[r])
        if len(vals) == 1 and next(iter(vals)) != bg:
            line_row, line_color = r, input_grid[r][0]
            break
    if line_row is None:
        return {}

    # Objects below the divider, grouped by color (each color = one object;
    # the arrow may have a diagonally-detached tip, so we do NOT rely on
    # 4-connectivity to keep it whole). Exclude bg and the divider color.
    by_color = defaultdict(list)
    for r in range(line_row + 1, H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != line_color:
                by_color[v].append((r, c))
    below = [(col, cells) for col, cells in by_color.items()]
    if len(below) != 2:
        return {}

    # Identify the arrow: it is the component with a vertical bar -- the column
    # that appears most often within it has the maximal run length.
    def bar_run(cells):
        by_col = defaultdict(list)
        for r, c in cells:
            by_col[c].append(r)
        best = 0
        for c, rs in by_col.items():
            rs.sort()
            run = cur = 1
            for i in range(1, len(rs)):
                cur = cur + 1 if rs[i] == rs[i - 1] + 1 else 1
                run = max(run, cur)
            best = max(best, run)
        return best

    below.sort(key=lambda kc: bar_run(kc[1]), reverse=True)
    arrow_color, arrow_cells = below[0]
    obj_color, obj_cells = below[1]

    # Arrow vertical-bar column = most frequent column among arrow cells.
    bar_col = Counter(c for _, c in arrow_cells).most_common(1)[0][0]

    # Shift the arrow straight up so the top of its bar reaches row 0.
    bar_top = min(r for r, c in arrow_cells if c == bar_col)
    arrow_shift = -bar_top

    T = {}
    new_cells = set()

    for r, c in arrow_cells:
        nr, nc = r + arrow_shift, c
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = arrow_color
            new_cells.add((nr, nc))

    # The arrow's diagonal tip = arrow cells not on the bar column. Its
    # "upper" cell (smallest row) is the landing anchor.
    tip_cells = [(r, c) for r, c in arrow_cells if c != bar_col]
    tip_upper = min(tip_cells, key=lambda rc: rc[0])
    anchor_r = tip_upper[0] + arrow_shift
    anchor_c = tip_upper[1]

    # Place the object so its bounding-box bottom-right corner lands on anchor.
    maxr = max(r for r, c in obj_cells)
    maxc = max(c for r, c in obj_cells)
    dr, dc = anchor_r - maxr, anchor_c - maxc
    for r, c in obj_cells:
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = obj_color
            new_cells.add((nr, nc))

    # Clear every original object cell below the divider that is not reused.
    for _, cells in below:
        for r, c in cells:
            if (r, c) not in new_cells:
                T[(r, c)] = bg

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
