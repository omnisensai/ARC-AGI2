"""Canonical ARC solver for puzzle dc2aa30b.

Structure: the grid is a 3x3 arrangement of small square blocks separated by
single full lines of a uniform separator color. The transformation rearranges
(permutes) the blocks. Reading-order of the OUTPUT block positions, the blocks
are sorted so that the count of one foreground color increases along a fixed
fill order: within each row from right to left, rows from top to bottom. The
lowest-count block lands at the top-right; the highest at the bottom-left.

Canonical latent-T form: infer_T builds a mask {(r,c): new_color} that overwrites
only the (non-separator) block cells with the permuted contents; apply_T copies
the input and applies the mask.
"""

from collections import Counter


def _find_separators(grid):
    """Return (sep_color, sep_rows, sep_cols) for the uniform separator lines."""
    H, W = len(grid), len(grid[0])
    # Candidate separator color: the color that fills entire rows or columns.
    full_row_colors = Counter()
    for r in range(H):
        s = set(grid[r])
        if len(s) == 1:
            full_row_colors[next(iter(s))] += 1
    full_col_colors = Counter()
    for c in range(W):
        s = set(grid[r][c] for r in range(H))
        if len(s) == 1:
            full_col_colors[next(iter(s))] += 1
    combined = full_row_colors + full_col_colors
    if not combined:
        return None, [], []
    sep_color = combined.most_common(1)[0][0]
    sep_rows = [r for r in range(H) if all(v == sep_color for v in grid[r])]
    sep_cols = [c for c in range(W) if all(grid[r][c] == sep_color for r in range(H))]
    return sep_color, sep_rows, sep_cols


def _segments(length, seps):
    """Split [0,length) into contiguous runs separated by the sep indices."""
    segs = []
    cur = []
    sset = set(seps)
    for i in range(length):
        if i in sset:
            if cur:
                segs.append(cur)
                cur = []
        else:
            cur.append(i)
    if cur:
        segs.append(cur)
    return segs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sep_color, sep_rows, sep_cols = _find_separators(input_grid)

    row_segs = _segments(H, sep_rows)
    col_segs = _segments(W, sep_cols)

    # Require a grid of blocks to operate on.
    if not row_segs or not col_segs:
        return {}

    nbr = len(row_segs)
    nbc = len(col_segs)

    # Extract block contents as lists of (rows, cols) coordinate windows.
    blocks = {}
    for bi, rs in enumerate(row_segs):
        for bj, cs in enumerate(col_segs):
            cells = [(r, c) for r in rs for c in cs]
            blocks[(bi, bj)] = cells

    # Determine the two foreground colors present in blocks.
    fg = Counter()
    for cells in blocks.values():
        for (r, c) in cells:
            fg[input_grid[r][c]] += 1
    # Sorting key color: the highest-valued foreground color. Blocks are ordered
    # ascending by how many cells of that color they contain.
    key_color = max(fg) if fg else None

    def block_count(cells):
        return sum(1 for (r, c) in cells if input_grid[r][c] == key_color)

    # Fill order over block positions: rows top->bottom, columns right->left.
    fill_positions = [(bi, bj) for bi in range(nbr) for bj in range(nbc - 1, -1, -1)]

    # Sort source blocks ascending by key_color count.
    ordered_keys = sorted(blocks.keys(), key=lambda k: block_count(blocks[k]))

    # Build latent mask: assign sorted source-block contents to fill positions.
    T = {}
    for slot_idx, dest_key in enumerate(fill_positions):
        src_key = ordered_keys[slot_idx]
        src_cells = blocks[src_key]
        dest_cells = blocks[dest_key]
        for (sr, sc), (dr, dc) in zip(src_cells, dest_cells):
            T[(dr, dc)] = input_grid[sr][sc]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
