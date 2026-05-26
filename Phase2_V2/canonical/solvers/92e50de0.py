from collections import Counter


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _separator_color(grid):
    """The grid color forming full separator rows (or columns)."""
    H, W = len(grid), len(grid[0])
    rowfull = Counter()
    for r in range(H):
        vals = set(grid[r])
        if len(vals) == 1:
            rowfull[next(iter(vals))] += 1
    if rowfull:
        return rowfull.most_common(1)[0][0]
    colfull = Counter()
    for c in range(W):
        vals = set(grid[r][c] for r in range(H))
        if len(vals) == 1:
            colfull[next(iter(vals))] += 1
    return colfull.most_common(1)[0][0] if colfull else None


def _blocks(grid, sep):
    """Spans of consecutive non-separator rows and columns (the grid cells)."""
    H, W = len(grid), len(grid[0])

    def spans(is_sep_line):
        out = []
        start = None
        for i in range(len(is_sep_line)):
            if is_sep_line[i]:
                if start is not None:
                    out.append((start, i))
                    start = None
            else:
                if start is None:
                    start = i
        if start is not None:
            out.append((start, len(is_sep_line)))
        return out

    row_sep = [all(grid[r][c] == sep for c in range(W)) for r in range(H)]
    col_sep = [all(grid[r][c] == sep for r in range(H)) for c in range(W)]
    return spans(row_sep), spans(col_sep)


def infer_T(input_grid):
    """Latent mask: replicate the single decorated cell's pattern into every
    grid cell whose block-row and block-col both differ from the source by an
    even number (same checkerboard parity)."""
    H, W = len(input_grid), len(input_grid[0])
    sep = _separator_color(input_grid)
    row_blocks, col_blocks = _blocks(input_grid, sep)

    cnt = Counter()
    for row in input_grid:
        for v in row:
            if v != sep:
                cnt[v] += 1
    bg = cnt.most_common(1)[0][0]

    # locate the source cell (block holding non-background, non-separator cells)
    src = None
    for bi, (r0, r1) in enumerate(row_blocks):
        for bj, (c0, c1) in enumerate(col_blocks):
            if any(input_grid[r][c] not in (sep, bg)
                   for r in range(r0, r1) for c in range(c0, c1)):
                src = (bi, bj, r0, r1, c0, c1)
                break
        if src:
            break

    T = [[None] * W for _ in range(H)]
    if src is None:
        return T
    sbi, sbj, sr0, sr1, sc0, sc1 = src
    bh, bw = sr1 - sr0, sc1 - sc0
    pattern = [[input_grid[sr0 + dr][sc0 + dc] for dc in range(bw)]
               for dr in range(bh)]

    for bi, (r0, r1) in enumerate(row_blocks):
        if (bi - sbi) % 2 != 0:
            continue
        for bj, (c0, c1) in enumerate(col_blocks):
            if (bj - sbj) % 2 != 0:
                continue
            for dr in range(min(bh, r1 - r0)):       # clip partial edge cells
                for dc in range(min(bw, c1 - c0)):
                    T[r0 + dr][c0 + dc] = pattern[dr][dc]
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
