def _bars(grid):
    """Find vertical contiguous runs of non-7 cells, per column."""
    H, W = len(grid), len(grid[0])
    res = []
    for c in range(W):
        r = 0
        while r < H:
            if grid[r][c] != 7:
                start = r
                cells = []
                while r < H and grid[r][c] != 7:
                    cells.append(grid[r][c])
                    r += 1
                res.append((c, start, r - 1, cells))
            else:
                r += 1
    return res


def infer_T(input_grid):
    """Latent transformation mask: dict {(r,c): new_color}.

    The grid contains many vertical bars made of color 8. Exactly one bar
    (the source) also contains a contiguous 9-segment at one of its ends.
    The 9s point in the direction of that end. The target bar is the unique
    pure-8 bar whose length equals the source bar length + 2; into it we paint
    a 9-segment of length (source_9_count + 1) starting from the same end the
    source 9s pointed to. The source bar is fully reverted to 8.
    """
    bars = _bars(input_grid)
    T = {}

    sources = [b for b in bars if 9 in b[3]]
    if not sources:
        return T
    src = sources[0]
    sc, ss, se, scells = src
    src_len = len(scells)
    src_nine = scells.count(9)
    nine_at_top = scells[0] == 9

    # Revert the source bar entirely to 8.
    for k, r in enumerate(range(ss, se + 1)):
        if scells[k] == 9:
            T[(r, sc)] = 8

    # Target: unique pure-8 bar with length == src_len + 2.
    candidates = [b for b in bars if 9 not in b[3] and len(b[3]) == src_len + 2]
    if len(candidates) != 1:
        return T
    tc, ts, te, tcells = candidates[0]
    paint_len = src_nine + 1

    if nine_at_top:
        rows = range(ts, ts + paint_len)
    else:
        rows = range(te - paint_len + 1, te + 1)
    for r in rows:
        T[(r, tc)] = 9

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
