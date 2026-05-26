def _neighbors8(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                yield r + dr, c + dc


def _components(grid, colors):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colors and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] not in colors:
                        continue
                    seen.add((y, x))
                    comp.append((y, x))
                    for ny, nx in _neighbors8(y, x):
                        stack.append((ny, nx))
                comps.append(sorted(comp))
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # legend = the connected block containing 9/1
    legends = _components(input_grid, {9, 1})
    T = {}
    if not legends:
        return T
    legend = max(legends, key=len)
    lr = sorted(set(r for r, c in legend))
    lc = sorted(set(c for r, c in legend))
    # legend bottom-row colors, left to right (9 or 1)
    bottom_colors = [input_grid[lr[-1]][c] for c in lc]

    # remove legend
    for (r, c) in legend:
        T[(r, c)] = bg

    # snakes = 5-objects
    snakes = _components(input_grid, {5})

    # --- placement heuristic (best-effort) ---
    # Determine bar anchors: for each snake, find diagonal tip columns and draw a 3-tall
    # vertical bar extending away from the body.
    bars = []  # list of (col, [r0,r1,r2])  ; rows top->bottom

    fivecells = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5)

    # heuristic: a "marked" snake is one whose bounding box spans diagonally (h>1 and w>1) and size>=5,
    # OR a vertical 2-cell stub. For each such snake we find tip columns.
    # We approximate the observed pattern: at a snake's extreme corner along its main diagonal,
    # shoot a vertical 3-bar of 9s.
    for s in snakes:
        sset = set(s)
        rs = [r for r, c in s]
        cs = [c for r, c in s]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        if len(s) < 5 and not (w == 1 and h == 2):
            continue
        # main diagonal sign: correlation of (r,c)
        # tip A = cell with max (r+c)? tip B = min(r+c)? Use both diagonal extremes.
        # find the up-tip: cell with min r among extreme; emit bar above topmost cell of its column
        # We emit at the topmost cell column and bottommost cell column.
        topmost = min(s, key=lambda p: (p[0], p[1]))
        botmost = max(s, key=lambda p: (p[0], p[1]))
        # up bar at topmost's column
        tc = topmost[1]
        col5 = sorted(r for (r, c) in fivecells if c == tc)
        if col5:
            top = col5[0]
            bars.append((tc, [top - 3, top - 2, top - 1]))
        # down bar at botmost's column
        bc = botmost[1]
        col5b = sorted(r for (r, c) in fivecells if c == bc)
        if col5b:
            bot = col5b[-1]
            bars.append((bc, [bot - 1, bot, bot + 1]))

    # assign colors: all bar columns sorted left-to-right get bottom_colors in order
    bars_by_col = {}
    for col, rows in bars:
        bars_by_col[col] = rows  # dedup by column
    ordered_cols = sorted(bars_by_col)
    for i, col in enumerate(ordered_cols):
        rows = bars_by_col[col]
        bottom_color = bottom_colors[i] if i < len(bottom_colors) else 9
        T[(rows[0], col)] = 9
        T[(rows[1], col)] = 9
        T[(rows[2], col)] = bottom_color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(input_grid), len(input_grid[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


