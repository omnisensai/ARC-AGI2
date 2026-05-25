def infer_T(input_grid):
    """Latent mask: recolor background to 5 and shift every horizontal run
    of a non-background color left by one cell.

    Returns (mask, bg) where mask is a dict {(r,c): new_color}.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    mask = {}
    for r in range(H):
        # Mark every background cell as becoming 5 (the new background).
        for c in range(W):
            if input_grid[r][c] == bg:
                mask[(r, c)] = 5
    for r in range(H):
        # Find each maximal horizontal run of a single non-bg color, then
        # paint that color shifted one cell to the left.
        c = 0
        while c < W:
            v = input_grid[r][c]
            if v == bg:
                c += 1
                continue
            c0 = c
            while c < W and input_grid[r][c] == v:
                c += 1
            for cc in range(c0, c):          # original run columns [c0, c-1]
                nc = cc - 1
                if 0 <= nc < W:
                    mask[(r, nc)] = v        # painted one to the left
            # The rightmost original column is vacated -> background 5,
            # unless a shifted color already claims it.
            last = c - 1
            if (r, last) not in mask or mask[(r, last)] == 5:
                if input_grid[r][last] == v and (last + 1 >= W or input_grid[r][last + 1] != v):
                    mask[(r, last)] = 5
    # Re-apply shifted colors so they win over vacated-cell 5 assignments
    for r in range(H):
        c = 0
        while c < W:
            v = input_grid[r][c]
            if v == bg:
                c += 1
                continue
            c0 = c
            while c < W and input_grid[r][c] == v:
                c += 1
            for cc in range(c0, c):
                nc = cc - 1
                if 0 <= nc < W:
                    mask[(r, nc)] = v
    return mask, bg


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named by the mask."""
    mask, bg = T
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
