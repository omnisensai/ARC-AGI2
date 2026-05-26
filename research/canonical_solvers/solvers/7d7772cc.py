"""Canonical solver for ARC puzzle 7d7772cc.

Rule
----
The grid contains a "box" enclosed by a border color and separated from a
"free" region by a single full straight line of that border color (the *bar*).
The cell-line just inside the box, adjacent to the bar, is a "key" sequence of
colored markers. The free region carries its own row/column of markers, one per
position along the bar.

For each free marker (indexed by its position along the bar):
  - if its color matches the key marker at the same index, it moves to the cell
    immediately outside the bar (box-adjacent target);
  - otherwise it moves to the far edge of the free region.
The marker's original cell is cleared to the free-region background.

infer_T produces a sparse mask {(r,c): new_color} and apply_T overwrites only
those cells.
"""

from collections import Counter


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1

    # Full single-color lines.
    full_rows = {r: input_grid[r][0]
                 for r in range(H) if len(set(input_grid[r])) == 1}
    full_cols = {c: input_grid[0][c]
                 for c in range(W)
                 if len(set(input_grid[r][c] for r in range(H))) == 1}

    # How many full lines each color participates in (the bar appears in the
    # fewest; background colors tend to span many full lines).
    line_color_count = Counter()
    for col in full_rows.values():
        line_color_count[col] += 1
    for col in full_cols.values():
        line_color_count[col] += 1

    # Bar candidates: a full line whose color occurs more than its own length,
    # i.e. it also forms the enclosing frame of the box.
    candidates = []
    for r, col in full_rows.items():
        if cnt[col] > W:
            candidates.append((col, 'row', r))
    for c, col in full_cols.items():
        if cnt[col] > H:
            candidates.append((col, 'col', c))
    candidates.sort(key=lambda x: line_color_count[x[0]])
    bar_color, bar_orient, bar_idx = candidates[0]

    def region_bg(cells):
        c = Counter(cells)
        c.pop(bar_color, None)
        return c.most_common(1)[0][0]

    T = {}

    if bar_orient == 'row':
        def side_has_frame(rng):
            return any(0 <= r < H and (input_grid[r][0] == bar_color
                                       or input_grid[r][W - 1] == bar_color)
                       for r in rng)
        # The framed side is the box; the free region is the opposite side.
        free_dir = -1 if side_has_frame(range(bar_idx + 1, H)) else 1
        key_row = bar_idx - free_dir
        key = {c: input_grid[key_row][c] for c in range(W)}
        free_rows = range(0, bar_idx) if free_dir == -1 else range(bar_idx + 1, H)
        free_bg = region_bg([input_grid[r][c]
                             for r in free_rows for c in range(W)])
        adj_row = bar_idx + free_dir
        far_row = 0 if free_dir == -1 else H - 1
        for c in range(W):
            kc = key.get(c)
            r_iter = (range(bar_idx - 1, -1, -1) if free_dir == -1
                      else range(bar_idx + 1, H))
            for r in r_iter:
                v = input_grid[r][c]
                if v != free_bg and v != bar_color:
                    T[(r, c)] = free_bg
                    target = adj_row if v == kc else far_row
                    T[(target, c)] = v
                    break
    else:
        bar_c = bar_idx

        def side_has_frame(rng):
            return any(0 <= c < W and (input_grid[0][c] == bar_color
                                       or input_grid[H - 1][c] == bar_color)
                       for c in rng)
        free_dir = -1 if side_has_frame(range(bar_c + 1, W)) else 1
        key_col = bar_c - free_dir
        key = {r: input_grid[r][key_col] for r in range(H)}
        free_cols = range(0, bar_c) if free_dir == -1 else range(bar_c + 1, W)
        free_bg = region_bg([input_grid[r][c]
                             for r in range(H) for c in free_cols])
        adj_col = bar_c + free_dir
        far_col = 0 if free_dir == -1 else W - 1
        for r in range(H):
            kr = key.get(r)
            c_iter = (range(bar_c - 1, -1, -1) if free_dir == -1
                      else range(bar_c + 1, W))
            for c in c_iter:
                v = input_grid[r][c]
                if v != free_bg and v != bar_color:
                    T[(r, c)] = free_bg
                    target = adj_col if v == kr else far_col
                    T[(r, target)] = v
                    break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
