def infer_T(input_grid):
    """Compute a latent transformation mask {(r,c): new_color}.

    Structure: one fully-filled row is a two-color 'template' pattern. Each other
    non-empty row holds only a short non-bg prefix (the 'key') that maps the
    template's colors to new ones; the rest of that row is reconstructed by
    substituting the template's colors through the key-derived color map.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # template row: fully filled (no background cells), at least one non-bg.
    template_r = None
    for r in range(H):
        row = input_grid[r]
        if all(v != bg for v in row) and any(v != bg for v in row):
            template_r = r
            break

    T = {}
    if template_r is None:
        return T
    template = input_grid[template_r]

    for r in range(H):
        if r == template_r:
            continue
        row = input_grid[r]
        # measure the leading run of non-bg cells (the key prefix).
        prefix_len = 0
        for c in range(W):
            if row[c] != bg:
                prefix_len = c + 1
            else:
                break
        if prefix_len == 0:
            continue
        # remainder must be empty for this to be a partial 'key' row.
        if any(row[c] != bg for c in range(prefix_len, W)):
            continue
        # derive template-color -> key-color map from the aligned prefix.
        cmap = {}
        consistent = True
        for c in range(prefix_len):
            tc, nc = template[c], row[c]
            if tc in cmap and cmap[tc] != nc:
                consistent = False
                break
            cmap[tc] = nc
        if not consistent:
            continue
        # reconstruct the rest of the row via the color substitution.
        for c in range(prefix_len, W):
            tc = template[c]
            if tc in cmap:
                T[(r, c)] = cmap[tc]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
