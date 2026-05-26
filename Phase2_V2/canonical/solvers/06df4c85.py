def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    sep = input_grid[0][2]
    # background is most common non-sep color (usually 0)
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = 0
    if 0 not in counts:
        bg = max((k for k in counts if k != sep), key=counts.get)

    # block lattice: cells are 2x2, separated by 1-wide separator lines
    BR = (H + 1) // 3
    BC = (W + 1) // 3

    # representative color of each block = its top-left cell
    bcolor = [[input_grid[br * 3][bc * 3] for bc in range(BC)] for br in range(BR)]

    # group the colored blocks by color
    by_color = {}
    for br in range(BR):
        for bc in range(BC):
            v = bcolor[br][bc]
            if v != bg and v != sep:
                by_color.setdefault(v, []).append((br, bc))

    # for each same-color pair sharing a block-row or block-column,
    # fill every block between them along that line
    block_mask = {}
    for color, cells in by_color.items():
        n = len(cells)
        for i in range(n):
            for j in range(i + 1, n):
                r1, c1 = cells[i]
                r2, c2 = cells[j]
                if r1 == r2:
                    for c in range(min(c1, c2), max(c1, c2) + 1):
                        block_mask[(r1, c)] = color
                elif c1 == c2:
                    for r in range(min(r1, r2), max(r1, r2) + 1):
                        block_mask[(r, c1)] = color

    # expand the block mask onto the 2x2 cell region of each block
    T = [[None] * W for _ in range(H)]
    for (br, bc), color in block_mask.items():
        r0, c0 = br * 3, bc * 3
        for dr in range(2):
            for dc in range(2):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < H and 0 <= c < W:
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
