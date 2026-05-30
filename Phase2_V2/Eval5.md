████████████████████████████████████████████████████████████████████████████████
  PUZZLE: 00d62c1b   MODE: PASS
  Model raw len: 1522 chars / 50 lines
  Canonical len: 1513 chars / 50 lines
████████████████████████████████████████████████████████████████████████████████

┌───────────────────────────────────────────────────────────────────────────────
│  CANONICAL (training target)
└───────────────────────────────────────────────────────────────────────────────
def infer_T(input_grid):
    """Compute mask of background cells enclosed (not border-reachable) -> color 4."""
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # flood fill bg cells reachable from the border (4-connectivity)
    reachable = set()
    stack = []
    for r in range(H):
        for c in (0, W - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in reachable:
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != bg:
            continue
        reachable.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    # enclosed bg cells = bg cells not reachable from border
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg and (r, c) not in reachable:
                T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


┌───────────────────────────────────────────────────────────────────────────────
│  MODEL OUTPUT (raw)
└───────────────────────────────────────────────────────────────────────────────
def infer_T(input_grid):
    """Compute mask of background cells enclosed (not border-reachable) -> color 4."""
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=lambda k: counts[k])
    # flood fill bg cells reachable from the border (4-connectivity)
    reachable = set()
    stack = []
    for r in range(H):
        for c in (0, W - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if input_grid[r][c] == bg:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in reachable:
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != bg:
            continue
        reachable.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    # enclosed bg cells = bg cells not reachable from border
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg and (r, c) not in reachable:
                T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)



████████████████████████████████████████████████████████████████████████████████
  PUZZLE: 09629e4f   MODE: EMPTY_OR_INVALID
  Model raw len: 1917 chars / 66 lines
  Canonical len: 3144 chars / 96 lines
████████████████████████████████████████████████████████████████████████████████

┌───────────────────────────────────────────────────────────────────────────────
│  CANONICAL (training target)
└───────────────────────────────────────────────────────────────────────────────
def _bands(line_is_sep, n):
    spans = []
    start = None
    for i in range(n):
        if line_is_sep[i]:
            if start is not None:
                spans.append((start, i))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        spans.append((start, n))
    return spans


def infer_T(input_grid):
    """
    Infer the latent fill mask.

    The grid is a 3x3 arrangement of equal sub-blocks separated by full lines
    of the separator color (5). Exactly one block lacks the marker color 8 --
    that is the 'key' block. Inside the key block, each fill color (any color
    that is not background 0, not separator 5, not marker 8) occupies one cell
    position (r,c); that means the block sitting at grid-position (r,c) must be
    filled entirely with that color. Every other block is cleared to 0.

    Returns T as a 2D grid of None / int: None = leave cell unchanged
    (separators), int = overwrite with that color.
    """
    H, W = len(input_grid), len(input_grid[0])
    sep = 5

    # Identify separator rows / cols (fully separator-colored lines).
    row_sep = [all(input_grid[r][c] == sep for c in range(W)) for r in range(H)]
    col_sep = [all(input_grid[r][c] == sep for r in range(H)) for c in range(W)]

    row_bands = _bands(row_sep, H)
    col_bands = _bands(col_sep, W)

    T = [[None] * W for _ in range(H)]
    # If structure is not the expected 3x3 of blocks, leave mask empty.
    if len(row_bands) != 3 or len(col_bands) != 3:
        return T

    # Collect blocks.
    blocks = {}
    for bi, (r0, r1) in enumerate(row_bands):
        for bj, (c0, c1) in enumerate(col_bands):
            blocks[(bi, bj)] = (r0, r1, c0, c1)

    # Find the key block: the one with no marker color 8.
    key = None
    for k, (r0, r1, c0, c1) in blocks.items():
        has8 = any(input_grid[r][c] == 8 for r in range(r0, r1) for c in range(c0, c1))
        if not has8:
            key = k
            break
    if key is None:
        return T

    kr0, kr1, kc0, kc1 = blocks[key]
    kh, kw = kr1 - kr0, kc1 - kc0

    # Build a fill-color map per block position from the key block's cell layout.
    # Position (i,j) within the key block -> block (i,j) gets that color.
    fill = {(bi, bj): 0 for bi in range(3) for bj in range(3)}
    for i in range(kh):
        for j in range(kw):
            v = input_grid[kr0 + i][kc0 + j]
            if v not in (0, sep, 8) and (i, j) in fill:
                fill[(i, j)] = v

    # Write the mask: every cell of each block set to its fill color.
    for (bi, bj), (r0, r1, c0, c1) in blocks.items():
        color = fill[(bi, bj)]
        for r in range(r0, r1):
            for c in range(c0, c1):
                T[r][c] = color

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


┌───────────────────────────────────────────────────────────────────────────────
│  MODEL OUTPUT (raw)
└───────────────────────────────────────────────────────────────────────────────
def _bands(line_is_sep, n):
    spans = []
    start = None
    for i in range(n):
        if line_is_sep[i]:
            if start is None:
                continue
            spans.append((start, i))
            start = None
        elif start is None:
            start = i
    if start0 None:
        spans.append((start, n))
    return spans


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sep_row = [all(input_grid[R][C] == 5 for C in range(W)) for R in range(H)}
    sep_col = [all(input_grid[R][C] == 5 for R in range(H)) for C in range(W)}

    row_spans = _bands(sep_row, H)
    col_spans = _bands(sep_col, W)

    # Identify seed row: a non-separator row containing non-zero cells.
    # Seed rows are 'home' row frames regions for the transformation.
    seed_row = None
    for span in row_spans:
        r0, r1 = span
        if any(input_grid[r][c] != 0 for r in range(r0, r1)):
            seed_row = span
            break

    T = [[None] * W for _ in range(H)]
    if seed_row is None:
        return T

    sr0, sr1 = seed_row
    home_cols = [c for c in range(W) if input_grid[sr0][c] != 0 and 5 not in input_grid[sr0][c]]

    for span in row_spans:
        r0, r1 = span
        if r0 == sr0 and r1 == sr1:
            continue
        # Fill the whole region with the home-column color pattern anchored at
        # the seed row's home columns.
        home_vals = [input_grid[sr0][c] for c in home_cols]
        for c, v in zip(home_cols, home_vals):
            for rr in range(r0, r1):
                T[rr][c] = v
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    for r in range(H):
        for c in range(W):
            if T[r][c] is None:
                continue
            input_grid[r][c] = T[r][c]
    return input_grid


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)



████████████████████████████████████████████████████████████████████████████████
  PUZZLE: 12422b43   MODE: EMPTY_OR_INVALID
  Model raw len: 8473 chars / 8 lines
  Canonical len: 1492 chars / 52 lines
████████████████████████████████████████████████████████████████████████████████

┌───────────────────────────────────────────────────────────────────────────────
│  CANONICAL (training target)
└───────────────────────────────────────────────────────────────────────────────
def infer_T(input_grid):
    """Infer the latent overwrite mask T as {(r,c): color}.

    Structure: column 0 holds a vertical run of `k` 5-markers. A non-zero
    'pattern' occupies the top rows (cols >= 1). The first `k` pattern rows
    form a seed that is tiled downward (cols >= 1 only) starting just below the
    last pattern row, filling the remaining grid.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # k = number of 5 markers in column 0
    k = sum(1 for r in range(H) if input_grid[r][0] == 5)

    # rows that contain any non-zero content in cols >= 1 (the pattern)
    pat_rows = [r for r in range(H)
                if any(input_grid[r][c] != 0 for c in range(1, W))]

    T = {}
    if k <= 0 or not pat_rows:
        return T

    pat_end = max(pat_rows)

    # seed = first k pattern rows (cols >= 1 only)
    seed = []
    for r in range(k):
        seed.append([input_grid[r][c] for c in range(W)])

    # tile the seed downward starting just after the pattern
    start = pat_end + 1
    for i, r in enumerate(range(start, H)):
        srow = seed[i % k]
        for c in range(1, W):
            T[(r, c)] = srow[c]

    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


┌───────────────────────────────────────────────────────────────────────────────
│  MODEL OUTPUT (raw)
└───────────────────────────────────────────────────────────────────────────────
def infer_T(input_grid):
    """Infer the latent overwrite mask T as {(r,c): color}.

    Structure: column 0 holds a vertical run of `k` 5-markers. A non-zero
    'pattern' occupies the top rows (cols >= 1). The first `k` pattern rows
    form a seed that is is is is gets replicated down the grid. Every row from the
    pattern downward is000 is is is00 is (i == 0..pattern_len-) is00000 is is00
    is0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000


████████████████████████████████████████████████████████████████████████████████
  PUZZLE: 13f06aa5   MODE: EMPTY_OR_INVALID
  Model raw len: 8769 chars / 12 lines
  Canonical len: 4492 chars / 134 lines
████████████████████████████████████████████████████████████████████████████████

┌───────────────────────────────────────────────────────────────────────────────
│  CANONICAL (training target)
└───────────────────────────────────────────────────────────────────────────────
"""Canonical solver for ARC puzzle 13f06aa5.

Rule (same-size):
  The grid is a uniform background containing several 8-cell "arrow" objects.
  Each arrow is a 5-long bar plus a 3-long bar forming an arrowhead, and carries
  exactly one minority-colored "marker" cell. The arrow points along its long
  axis toward the side that holds the marker (the narrow head side):
      - marker above centroid  -> points UP    -> paints the TOP edge
      - marker below centroid  -> points DOWN  -> paints the BOTTOM edge
      - marker left  of centroid -> points LEFT  -> paints the LEFT edge
      - marker right of centroid -> points RIGHT -> paints the RIGHT edge
  For each arrow with marker color M:
      1. paint the whole target edge with M;
      2. shoot a dashed ray of M from the marker toward that edge, painting
         every other cell (marker+2, marker+4, ...) up to the edge.
  Any grid corner shared by two painted edges becomes 0.
  The original arrow objects are left untouched.

Canonical latent-T form: infer_T builds the explicit overwrite mask
{(r,c): color}; apply_T copies the input and writes only the masked cells.
"""

from collections import Counter


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or grid[y][x] == bg:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    grid = input_grid
    H, W = len(grid), len(grid[0])
    bg = _background(grid)

    T = {}                 # (r,c) -> color overwrite mask
    edges = {}             # side -> color, for corner resolution

    for cells in _components(grid, bg):
        colors = Counter(grid[y][x] for y, x in cells)
        # marker = the unique minority cell within this object
        markers = [col for col, n in colors.items() if n == 1]
        if not markers:
            continue
        M = markers[0]
        (my, mx) = next((y, x) for y, x in cells if grid[y][x] == M)

        cy = sum(y for y, x in cells) / len(cells)
        cx = sum(x for y, x in cells) / len(cells)

        # pointing direction: marker sits on the head (narrow) side, offset
        # from the centroid along the object's long axis.
        if abs((my - cy)) >= abs((mx - cx)):
            dr = -1 if my < cy else 1
            dc = 0
        else:
            dr = 0
            dc = -1 if mx < cx else 1

        # 1) paint the whole target edge with M
        if dr == -1:
            side = "top"
            for c in range(W):
                T[(0, c)] = M
        elif dr == 1:
            side = "bottom"
            for c in range(W):
                T[(H - 1, c)] = M
        elif dc == -1:
            side = "left"
            for r in range(H):
                T[(r, 0)] = M
        else:
            side = "right"
            for r in range(H):
                T[(r, W - 1)] = M
        edges[side] = M

        # 2) dashed ray from marker toward the edge, every other cell
        ry, rx = my + 2 * dr, mx + 2 * dc
        while 0 <= ry < H and 0 <= rx < W:
            T[(ry, rx)] = M
            ry += 2 * dr
            rx += 2 * dc

    # 3) corners shared by two painted edges become 0
    corner_pairs = {
        (0, 0): ("top", "left"),
        (0, W - 1): ("top", "right"),
        (H - 1, 0): ("bottom", "left"),
        (H - 1, W - 1): ("bottom", "right"),
    }
    for (r, c), (a, b) in corner_pairs.items():
        if a in edges and b in edges:
            T[(r, c)] = 0

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


┌───────────────────────────────────────────────────────────────────────────────
│  MODEL OUTPUT (raw)
└───────────────────────────────────────────────────────────────────────────────
"""Canonical solver for ARC puzzle 13f06aa5.

Rule (same-size):
  The grid is a uniform background containing several 8-cell "arrow" objectses.
  Each arrow is a 5-long bar plus a 3-long bar forming an arrowhead, and carries
  exactly one minority-colored "marker" cell. The arrow points along along toward the
  side whose approach is, measured from the marker, sweeps the most background
  cells (the "d o'clock" direction around the marker). The transformation
  extends a straight line through the marker in that pointing direction until it
  leaves the grid, marking every background cell along2 along along on that boundary
  edge as part of the "tail". The original arrow object1 keeps its 8-cells; only the
  extended tail becomes the new grid's111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111


████████████████████████████████████████████████████████████████████████████████
  PUZZLE: 142ca369   MODE: EMPTY_OR_INVALID
  Model raw len: 8326 chars / 5 lines
  Canonical len: 4639 chars / 128 lines
████████████████████████████████████████████████████████████████████████████████

┌───────────────────────────────────────────────────────────────────────────────
│  CANONICAL (training target)
└───────────────────────────────────────────────────────────────────────────────
"""Solver for ARC puzzle 142ca369.

Structure of every input:
  * L-corners: a 2x2 window holding exactly three same-colored cells (one
    cell empty). Each L-corner is a diagonal EMITTER. It shoots a ray from the
    filled corner diagonally outward, away from the empty corner.
  * Straight lines (>=2 collinear cells), and isolated dots, are MIRRORS. A
    vertical line reflects the horizontal component of a passing diagonal ray
    (flips dx); a horizontal line reflects the vertical component (flips dy).
    A single dot can do either, depending on which side the ray grazes.
    When a ray reflects off a mirror it ALSO takes on the mirror's color.

Rays travel one diagonal cell at a time, recoloring blank cells they pass
through (the original objects are never overwritten). The latent mask T is the
dict of {(r,c): color} for every blank cell a ray paints.
"""


def _find_objects(g):
    """Return (L_corners, mirror_map).

    L_corners: list of (color, sorted-cells) for each 2x2-minus-one shape.
    mirror_map: dict cell -> (color, set_of_orientations) where orientation is
    'V' (vertical line), 'H' (horizontal line) or both (dot).
    """
    H, W = len(g), len(g[0])

    # L-corners detected directly from 2x2 windows (avoids merging two
    # same-colored corners that touch diagonally).
    L_set = set()
    for r in range(H - 1):
        for c in range(W - 1):
            win = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            nz = [g[y][x] for (y, x) in win if g[y][x] != 0]
            if len(nz) == 3 and len(set(nz)) == 1:
                cells = tuple(sorted((y, x) for (y, x) in win if g[y][x] != 0))
                L_set.add((nz[0], cells))

    Lcells = set()
    for _col, cells in L_set:
        Lcells.update(cells)

    mirror = {}
    # Horizontal runs (length >= 2) of one color, excluding L-corner cells.
    for r in range(H):
        c = 0
        while c < W:
            col = g[r][c]
            if col != 0 and (r, c) not in Lcells:
                cc = c
                while cc < W and g[r][cc] == col and (r, cc) not in Lcells:
                    cc += 1
                if cc - c >= 2:
                    for x in range(c, cc):
                        mirror[(r, x)] = (col, {'H'})
                c = cc
            else:
                c += 1
    # Vertical runs (length >= 2).
    for c in range(W):
        r = 0
        while r < H:
            col = g[r][c]
            if col != 0 and (r, c) not in Lcells:
                rr = r
                while rr < H and g[rr][c] == col and (rr, c) not in Lcells:
                    rr += 1
                if rr - r >= 2:
                    for y in range(r, rr):
                        mirror[(y, c)] = (col, {'V'})
                r = rr
            else:
                r += 1
    # Isolated dots act as point mirrors (either axis).
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and (r, c) not in Lcells and (r, c) not in mirror:
                mirror[(r, c)] = (g[r][c], {'V', 'H'})

    return sorted(L_set), mirror


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    L_corners, mirror = _find_objects(g)

    T = {}
    for col, cells in L_corners:
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        r0, c0 = min(rs), min(cs)
        full = {(r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1)}
        (my, mx), = full - set(cells)            # the empty corner
        oy = r0 if my == r0 + 1 else r0 + 1      # opposite (filled) corner
        ox = c0 if mx == c0 + 1 else c0 + 1
        dy, dx = oy - my, ox - mx                # diagonal direction (+-1,+-1)
        y, x = oy + dy, ox + dx                  # first cell beyond the corner
        cur = col

        steps = 0
        while 0 <= y < H and 0 <= x < W and steps < 4 * (H + W):
            steps += 1
            side = mirror.get((y, x + dx))       # vertical mirror to the side
            if side is not None and 'V' in side[1]:
                cur = side[0]
                dx = -dx
            ahead = mirror.get((y + dy, x))      # horizontal mirror ahead
            if ahead is not None and 'H' in ahead[1]:
                cur = ahead[0]
                dy = -dy
            if g[y][x] == 0:
                T[(y, x)] = cur                  # paint blank cell
            y += dy
            x += dx
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


┌───────────────────────────────────────────────────────────────────────────────
│  MODEL OUTPUT (raw)
└───────────────────────────────────────────────────────────────────────────────
"""Solver for ARC puzzle 142ca369.

Structure of every input input:
  - L-corners: an L of four identical non-background cells (a single color).
    exactly one cell is is is is is is0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
root@e3241538a7a6:/workspace/ARC-AGI2# 
