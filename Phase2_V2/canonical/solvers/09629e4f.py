def _bands(line_is_sep, n):
    spans = []
    start = None
    for i in range(n):
        if line_is_sep[i]:
            if start is not None:
                spans.append((start, i))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        spans.append((start, n))
    return spans


def infer_T(input_grid):
    """
    Infer the latent fill mask.

    The grid is a 3x3 arrangement of equal sub-blocks separated by full lines
    of the separator color (5). Exactly one block lacks the marker color 8 --
    that is the 'key' block. Inside the key block, each fill color (any color
    that is not background 0, not separator 5, not marker 8) occupies one cell
    position (r,c); that means the block sitting at grid-position (r,c) must be
    filled entirely with that color. Every other block is cleared to 0.

    Returns T as a 2D grid of None / int: None = leave cell unchanged
    (separators), int = overwrite with that color.
    """
    H, W = len(input_grid), len(input_grid[0])
    sep = 5

    # Identify separator rows / cols (fully separator-colored lines).
    row_sep = [all(input_grid[r][c] == sep for c in range(W)) for r in range(H)]
    col_sep = [all(input_grid[r][c] == sep for r in range(H)) for c in range(W)]

    row_bands = _bands(row_sep, H)
    col_bands = _bands(col_sep, W)

    T = [[None] * W for _ in range(H)]
    # If structure is not the expected 3x3 of blocks, leave mask empty.
    if len(row_bands) != 3 or len(col_bands) != 3:
        return T

    # Collect blocks.
    blocks = {}
    for bi, (r0, r1) in enumerate(row_bands):
        for bj, (c0, c1) in enumerate(col_bands):
            blocks[(bi, bj)] = (r0, r1, c0, c1)

    # Find the key block: the one with no marker color 8.
    key = None
    for k, (r0, r1, c0, c1) in blocks.items():
        has8 = any(input_grid[r][c] == 8 for r in range(r0, r1) for c in range(c0, c1))
        if not has8:
            key = k
            break
    if key is None:
        return T

    kr0, kr1, kc0, kc1 = blocks[key]
    kh, kw = kr1 - kr0, kc1 - kc0

    # Build a fill-color map per block position from the key block's cell layout.
    # Position (i,j) within the key block -> block (i,j) gets that color.
    fill = {(bi, bj): 0 for bi in range(3) for bj in range(3)}
    for i in range(kh):
        for j in range(kw):
            v = input_grid[kr0 + i][kc0 + j]
            if v not in (0, sep, 8) and (i, j) in fill:
                fill[(i, j)] = v

    # Write the mask: every cell of each block set to its fill color.
    for (bi, bj), (r0, r1, c0, c1) in blocks.items():
        color = fill[(bi, bj)]
        for r in range(r0, r1):
            for c in range(c0, c1):
                T[r][c] = color

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
