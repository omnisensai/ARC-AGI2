def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): color}.

    Structure: one row contains markers (non-background cells) of a single
    color. Treat its marker columns as 'level 0'. Repeatedly, two rows lower,
    place a mark at the midpoint of every pair of adjacent same-level marks
    that are exactly 2 columns apart. Colors of generated levels alternate
    6, marker_color, 6, marker_color, ... downward, until a level produces
    no marks or we run out of rows.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # locate the marker row and its color
    src_row = None
    mark_color = None
    for r in range(H):
        nonbg = [c for c in range(W) if input_grid[r][c] != bg]
        if nonbg:
            src_row = r
            mark_color = input_grid[r][nonbg[0]]
            break

    T = {}
    if src_row is None:
        return T

    cur = [c for c in range(W) if input_grid[src_row][c] == mark_color]
    colors = [6, mark_color]
    level = 0
    rr = src_row + 2
    while rr < H:
        newpos = []
        for a, b in zip(cur, cur[1:]):
            if b - a == 2:
                newpos.append((a + b) // 2)
        if not newpos:
            break
        col = colors[level % 2]
        for c in newpos:
            T[(rr, c)] = col
        cur = newpos
        level += 1
        rr += 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
