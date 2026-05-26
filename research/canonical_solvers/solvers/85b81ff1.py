def _structure(input_grid):
    """Detect background-separator columns and the data-cell column blocks."""
    H = len(input_grid)
    W = len(input_grid[0])
    # background is the most common color (the '0' grid lines / off cells)
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # separator columns are entirely background
    sep_cols = [c for c in range(W) if all(input_grid[r][c] == bg for r in range(H))]
    # group the remaining columns into contiguous blocks
    blocks = []
    cur = []
    for c in range(W):
        if c in sep_cols:
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(c)
    if cur:
        blocks.append(cur)
    return H, W, bg, sep_cols, blocks


def infer_T(input_grid):
    """
    Latent transformation: the data column-blocks are reordered by ascending
    'weight' (number of foreground data-cells they contain), ties broken by
    original position. Data cells live in odd rows at the right column of each
    block; even rows are fully foreground (structural).

    T is returned as a dict {(r,c): new_color} of every cell that must change.
    """
    H, W, bg, sep_cols, blocks = _structure(input_grid)

    # foreground color = the most common non-background color
    counts = {}
    for row in input_grid:
        for v in row:
            if v != bg:
                counts[v] = counts.get(v, 0) + 1
    fg = max(counts, key=counts.get) if counts else bg

    # rows that carry data: rows that are NOT entirely foreground within the blocks
    data_rows = []
    for r in range(H):
        full = all(input_grid[r][c] == fg for blk in blocks for c in blk)
        if not full:
            data_rows.append(r)

    # weight of each block = number of fg cells across data rows / data columns
    weights = []
    for bi, blk in enumerate(blocks):
        w = sum(1 for r in data_rows for c in blk if input_grid[r][c] == fg)
        weights.append(w)

    # new order of blocks: ascending weight, stable on original index
    order = sorted(range(len(blocks)), key=lambda i: (weights[i], i))

    # build the transformation mask: for each target block position, copy the
    # column contents of the source block (by relative column offset)
    T = {}
    for target_pos, src_idx in enumerate(order):
        tgt_blk = blocks[target_pos]
        src_blk = blocks[src_idx]
        for off in range(len(tgt_blk)):
            tc = tgt_blk[off]
            sc = src_blk[off]
            for r in range(H):
                T[(r, tc)] = input_grid[r][sc]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
