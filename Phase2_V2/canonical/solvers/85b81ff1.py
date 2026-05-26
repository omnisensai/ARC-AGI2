def _structure(input_grid):
    """Detect grid-line (separator) columns and the data-cell column blocks.

    The grid is a row of equal-width data blocks separated by single columns
    of a constant 'line' color. Several columns may be constant (e.g. a block's
    left edge that is always foreground), so the separator color is chosen as
    the constant-column color that partitions the grid into uniform-width blocks.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    const_cols = [c for c in range(W)
                  if all(input_grid[r][c] == input_grid[0][c] for r in range(H))]
    const_colors = set(input_grid[0][c] for c in const_cols)

    def partition(sep_set):
        blocks = []
        cur = []
        for c in range(W):
            if c in sep_set:
                if cur:
                    blocks.append(cur)
                    cur = []
            else:
                cur.append(c)
        if cur:
            blocks.append(cur)
        return blocks

    best = None
    for color in const_colors:
        sep_set = set(c for c in const_cols if input_grid[0][c] == color)
        blocks = partition(sep_set)
        if not blocks:
            continue
        uniform = len(set(len(b) for b in blocks)) == 1
        score = (uniform, len(blocks))
        if best is None or score > best[0]:
            best = (score, color, sep_set, blocks)
    _, bg, sep_cols, blocks = best
    return H, W, bg, sorted(sep_cols), blocks


def infer_T(input_grid):
    """Latent transformation: the data column-blocks are reordered by ascending
    'weight' (count of foreground data-cells), ties broken by original position.

    Returns T as a dict {(r, c): new_color} of every cell that changes.
    """
    H, W, bg, sep_cols, blocks = _structure(input_grid)

    # foreground color = most common non-line color
    counts = {}
    for row in input_grid:
        for v in row:
            if v != bg:
                counts[v] = counts.get(v, 0) + 1
    fg = max(counts, key=counts.get) if counts else bg

    # data rows = rows that are NOT fully foreground inside the blocks
    data_rows = [r for r in range(H)
                 if not all(input_grid[r][c] == fg for blk in blocks for c in blk)]

    # weight of each block = number of fg cells across data rows
    weights = [sum(1 for r in data_rows for c in blk if input_grid[r][c] == fg)
               for blk in blocks]

    # new order of blocks: ascending weight, stable on original index
    order = sorted(range(len(blocks)), key=lambda i: (weights[i], i))

    T = {}
    for target_pos, src_idx in enumerate(order):
        tgt_blk = blocks[target_pos]
        src_blk = blocks[src_idx]
        for off in range(len(tgt_blk)):
            tc, sc = tgt_blk[off], src_blk[off]
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
