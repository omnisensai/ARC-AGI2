"""Canonical solver for ARC puzzle fc10701f.

Structure: a background (6) grid containing a lattice of small 0-blocks, plus a
9-marker block and a 7-marker block that are aligned along a common "lane" (the
shared rows or shared columns of the 9 and 7 blocks). The 9 and 7 sit on opposite
ends of that lane.

Transformation:
  * The 7 block is removed (its origin cells revert to background).
  * The 9 block becomes color 7 (the marker travels to the 9's position).
  * Along the lane, every 0-lattice slot that lies strictly between the 9 and the
    7 (and is flanked by 0-blocks across the lane) is filled with color 2.

infer_T computes this purely from input structure; apply_T overwrites only the
masked cells.
"""


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def _bg(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    T = {}

    nine = _components(input_grid, 9)
    seven = _components(input_grid, 7)
    if not nine or not seven:
        return T
    nine = nine[0]
    seven = seven[0]

    nine_rows = set(r for r, _ in nine)
    nine_cols = set(c for _, c in nine)
    seven_rows = set(r for r, _ in seven)
    seven_cols = set(c for _, c in seven)

    # Lane orientation: marker blocks share columns -> vertical lane;
    # share rows -> horizontal lane.
    if nine_cols == seven_cols and nine_rows != seven_rows:
        vertical = True
        lane = sorted(nine_cols)            # lane columns
    elif nine_rows == seven_rows and nine_cols != seven_cols:
        vertical = False
        lane = sorted(nine_rows)            # lane rows
    else:
        # Fallback: pick the axis with equal extent.
        if nine_cols == seven_cols:
            vertical = True
            lane = sorted(nine_cols)
        else:
            vertical = False
            lane = sorted(nine_rows)

    # Positions of 0-blocks along the lane axis.
    zeros = _components(input_grid, 0)

    if vertical:
        # Lane runs along columns `lane`; vary by row.
        n_pos = sorted(nine_rows)
        s_pos = sorted(seven_rows)
        lo, hi = sorted((n_pos[0], s_pos[0]))
        a, b = min(n_pos[-1], s_pos[-1]), max(n_pos[0], s_pos[0])
        # strict-between range along the row axis
        between_lo = min(n_pos[-1], s_pos[-1])
        between_hi = max(n_pos[0], s_pos[0])

        for cells in zeros:
            rs = set(r for r, _ in cells)
            cs = set(c for _, c in cells)
            # This 0-block must be on one side of the lane columns.
            for r in rs:
                if between_lo < r < between_hi:
                    # check the lane cells at this row are background and
                    # flanked by 0-blocks across the lane
                    if all(input_grid[r][c] == bg for c in lane):
                        # require a 0-block on both sides of the lane in this row
                        left = any(input_grid[r][c] == 0 for c in range(0, lane[0]))
                        right = any(input_grid[r][c] == 0 for c in range(lane[-1] + 1, W))
                        if left and right:
                            for c in lane:
                                T[(r, c)] = 2
    else:
        n_pos = sorted(nine_cols)
        s_pos = sorted(seven_cols)
        between_lo = min(n_pos[-1], s_pos[-1])
        between_hi = max(n_pos[0], s_pos[0])

        for cells in zeros:
            cs = set(c for _, c in cells)
            for c in cs:
                if between_lo < c < between_hi:
                    if all(input_grid[r][c] == bg for r in lane):
                        up = any(input_grid[r][c] == 0 for r in range(0, lane[0]))
                        down = any(input_grid[r][c] == 0 for r in range(lane[-1] + 1, H))
                        if up and down:
                            for r in lane:
                                T[(r, c)] = 2

    # Remove the 7 block (revert to background).
    for (r, c) in seven:
        T[(r, c)] = bg
    # The 9 block becomes color 7.
    for (r, c) in nine:
        T[(r, c)] = 7

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
