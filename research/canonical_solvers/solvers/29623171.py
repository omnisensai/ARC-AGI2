def _separators(grid):
    H, W = len(grid), len(grid[0])
    # a separator color is one whose cells form full rows AND full columns (grid lines)
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    sep_rows, sep_cols = [], []
    for r in range(H):
        vals = set(grid[r])
        if len(vals) == 1:
            sep_rows.append((r, next(iter(vals))))
    for c in range(W):
        vals = set(grid[r][c] for r in range(H))
        if len(vals) == 1:
            sep_cols.append((c, next(iter(vals))))
    # the separator color is the value that appears in both a full row and a full col
    row_colors = set(v for _, v in sep_rows)
    col_colors = set(v for _, v in sep_cols)
    common = row_colors & col_colors
    sep_color = None
    if common:
        sep_color = max(common, key=lambda v: counts.get(v, 0))
    return sep_color


def _block_spans(grid, sep_color):
    H, W = len(grid), len(grid[0])
    sep_rows = set(r for r in range(H) if all(grid[r][c] == sep_color for c in range(W)))
    sep_cols = set(c for c in range(W) if all(grid[r][c] == sep_color for r in range(H)))
    # contiguous non-separator row ranges
    def spans(n, seps):
        res, start = [], None
        for i in range(n):
            if i in seps:
                if start is not None:
                    res.append((start, i))
                    start = None
            else:
                if start is None:
                    start = i
        if start is not None:
            res.append((start, n))
        return res
    return spans(H, sep_rows), spans(W, sep_cols)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sep_color = _separators(input_grid)
    rspans, cspans = _block_spans(input_grid, sep_color)

    # count marker cells per block; markers are any non-zero, non-separator color
    block_info = {}  # (bi,bj) -> (count, color)
    for bi, (r0, r1) in enumerate(rspans):
        for bj, (c0, c1) in enumerate(cspans):
            cnt = 0
            color = 0
            for r in range(r0, r1):
                for c in range(c0, c1):
                    v = input_grid[r][c]
                    if v != 0 and v != sep_color:
                        cnt += 1
                        color = v
            block_info[(bi, bj)] = (cnt, color)

    maxcount = max((cnt for cnt, _ in block_info.values()), default=0)
    fill_color = 0
    for cnt, color in block_info.values():
        if color != 0:
            fill_color = color
            break

    T = [[None] * W for _ in range(H)]
    for bi, (r0, r1) in enumerate(rspans):
        for bj, (c0, c1) in enumerate(cspans):
            cnt, _ = block_info[(bi, bj)]
            # winners (max count) get fully filled, others cleared to 0
            target = fill_color if (maxcount > 0 and cnt == maxcount) else 0
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if input_grid[r][c] != sep_color:
                        T[r][c] = target
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
