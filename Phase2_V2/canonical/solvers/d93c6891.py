"""Canonical latent-T solver for ARC puzzle d93c6891.

Rule (inferred from all train+test pairs):
  Each object is a rectangular block of 7s optionally accompanied by a
  1-cell-thick line of 5s lying along one face of the block (sharing that
  edge row/column and extending sideways past the block).

  For an object whose 5-line has length L:
    * the 5-line cells revert to the background color (4),
    * exactly L cells of the 7-block become 5, filled face-first: layer by
      layer (whole rows for a horizontal line, whole columns for a vertical
      line) starting from the face the line is attached to.
  Blocks with no 5-line are left untouched (stay 7).

  infer_T builds a {(r,c): new_color} mask from this structure; apply_T copies
  the input and overwrites only the masked cells.
"""


def _components(grid, colors):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colors and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen:
                        continue
                    if not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] not in colors:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                out.append(cells)
    return out


def _field_color(grid):
    # The "field" is the color in which the 5/7 markers are embedded: the most
    # common non-marker color found directly adjacent to any marker cell.
    H, W = len(grid), len(grid[0])
    nb = {}
    for r in range(H):
        for c in range(W):
            if grid[r][c] in (5, 7):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = r + dr, c + dc
                    if 0 <= a < H and 0 <= b < W:
                        v = grid[a][b]
                        if v not in (5, 7):
                            nb[v] = nb.get(v, 0) + 1
    if nb:
        return max(nb, key=nb.get)
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    grid = input_grid
    bg = _field_color(grid)
    T = {}  # latent transformation mask: (r,c) -> new color

    for comp in _components(grid, {5, 7}):
        sevens = [(r, c) for r, c in comp if grid[r][c] == 7]
        fives = [(r, c) for r, c in comp if grid[r][c] == 5]
        if not sevens:
            continue
        # block bounding box (cells are all 7 -> solid rectangle)
        rs = [r for r, c in sevens]
        cs = [c for r, c in sevens]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        height = r1 - r0 + 1
        width = c1 - c0 + 1

        if not fives:
            continue  # lone block keeps its 7s

        L = len(fives)

        # erase the 5-line (revert to background)
        for r, c in fives:
            T[(r, c)] = bg

        # determine line orientation and which face it attaches to
        line_rows = set(r for r, c in fives)
        line_cols = set(c for r, c in fives)
        horizontal = len(line_rows) == 1

        fill_cells = []
        if horizontal:
            lr = next(iter(line_rows))
            # attaches to top (lr == r0) or bottom (lr == r1)
            if abs(lr - r0) <= abs(lr - r1):
                row_order = list(range(r0, r1 + 1))            # fill from top
            else:
                row_order = list(range(r1, r0 - 1, -1))        # fill from bottom
            for r in row_order:
                for c in range(c0, c1 + 1):
                    fill_cells.append((r, c))
        else:
            lc = next(iter(line_cols))
            if abs(lc - c0) <= abs(lc - c1):
                col_order = list(range(c0, c1 + 1))            # fill from left
            else:
                col_order = list(range(c1, c0 - 1, -1))        # fill from right
            for c in col_order:
                for r in range(r0, r1 + 1):
                    fill_cells.append((r, c))

        # turn the first L block cells (face-first) into 5; the rest stay 7
        for (r, c) in fill_cells[:L]:
            T[(r, c)] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
