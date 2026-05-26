def infer_T(input_grid):
    """Latent mask: scattered dots slide along their row/col toward the
    full line of matching color, landing adjacent to it; unmatched dots vanish."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Detect full-row lines and full-column lines (uniform, non-background)
    row_lines = {}   # color -> row index
    col_lines = {}   # color -> col index
    for r in range(H):
        v = input_grid[r][0]
        if v != bg and all(input_grid[r][c] == v for c in range(W)):
            row_lines[v] = r
    for c in range(W):
        v = input_grid[0][c]
        if v != bg and all(input_grid[r][c] == v for r in range(H)):
            col_lines[v] = c

    horizontal = len(row_lines) >= len(col_lines)  # are the lines horizontal?
    lines = row_lines if horizontal else col_lines
    line_rows = set(row_lines.values())
    line_cols = set(col_lines.values())

    moves = []  # (old_rc, new_rc_or_None, color)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            if horizontal and r in line_rows:
                continue
            if (not horizontal) and c in line_cols:
                continue
            # scattered dot of color v
            if v not in lines:
                moves.append(((r, c), None, v))      # no matching line -> vanish
                continue
            if horizontal:
                lr = lines[v]
                new_rc = (lr - 1, c) if r < lr else (lr + 1, c)
            else:
                lc = lines[v]
                new_rc = (r, lc - 1) if c < lc else (r, lc + 1)
            moves.append(((r, c), new_rc, v))

    T = {}  # latent transformation mask: cell -> new color
    for (oldrc, _newrc, _v) in moves:
        T[oldrc] = bg
    for (_oldrc, newrc, v) in moves:
        if newrc is not None:
            T[newrc] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
