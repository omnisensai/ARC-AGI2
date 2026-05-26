def _bg_of(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    """Latent mask: a dict {(r,c): new_color}.

    Structure: the grid contains horizontal bands of "pattern" rows (rows with
    any non-background cell), separated by all-background rows. Within each
    maximal run of consecutive pattern rows the rows alternate between two
    types; the 2nd, 4th, ... row of each run is shifted right by one cell
    (vacated leftmost cell filled with the background color).
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg_of(input_grid)

    pattern_rows = [r for r in range(H)
                    if any(v != bg for v in input_grid[r])]

    # Maximal runs of consecutive pattern rows.
    runs, cur = [], []
    for r in range(H):
        if r in pattern_rows:
            cur.append(r)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)

    T = {}
    for run in runs:
        for i, r in enumerate(run):
            if i % 2 == 1:  # shift this row right by one
                for c in range(W):
                    T[(r, c)] = input_grid[r][c - 1] if c - 1 >= 0 else bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
