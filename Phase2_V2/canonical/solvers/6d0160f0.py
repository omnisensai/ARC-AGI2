def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): new_color}.

    The grid is a 3x3 arrangement of 3x3 cell-blocks separated by lines of 5s
    (rows/cols 3 and 7). Exactly one block contains a marker color 4. The
    position (i,j) of that 4 *within* its own block selects the destination
    block (i,j). The output clears every block, then copies the marker block's
    content into the destination block. Separator lines (5s) are untouched.
    """
    H, W = len(input_grid), len(input_grid[0])

    # block top-left coordinates: rows/cols 0,4,8 (skipping separators at 3,7)
    starts = [0, 4, 8]

    def block_content(br, bc):
        r0, c0 = starts[br], starts[bc]
        return [[input_grid[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

    # locate the block containing the marker (4) and the marker's in-block pos
    src = None
    pos4 = None
    for br in range(3):
        for bc in range(3):
            cell = block_content(br, bc)
            for i in range(3):
                for j in range(3):
                    if cell[i][j] == 4:
                        src = (br, bc)
                        pos4 = (i, j)

    T = {}
    if src is None:
        # no marker: clear every non-separator, non-zero cell
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] != 5 and input_grid[r][c] != 0:
                    T[(r, c)] = 0
        return T

    dst = pos4  # destination block index == marker position within its block
    src_cell = block_content(*src)

    # mask: clear all block cells, then stamp source content into dst block
    for br in range(3):
        for bc in range(3):
            r0, c0 = starts[br], starts[bc]
            for i in range(3):
                for j in range(3):
                    r, c = r0 + i, c0 + j
                    if (br, bc) == dst:
                        T[(r, c)] = src_cell[i][j]
                    else:
                        T[(r, c)] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
