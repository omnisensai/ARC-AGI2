def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid is partitioned into 2x2 blocks. Each block-row contains exactly
    one non-empty 2x2 motif, sitting at some block-column. The transformation
    reflects every motif's block-column across the vertical axis of the block
    grid (bc -> nbc-1-bc) while keeping its block-row and its 2x2 content
    unchanged. T is the dict of cells that change, mapping (r,c) -> new color.
    """
    H, W = len(input_grid), len(input_grid[0])
    bh, bw = 2, 2
    nbr, nbc = H // bh, W // bw

    # collect, per block-row, the source motif (block-col + 2x2 content)
    motifs = {}  # br -> (bc, content as list[list[int]])
    for br in range(nbr):
        for bc in range(nbc):
            content = [[input_grid[br * bh + a][bc * bw + b] for b in range(bw)]
                       for a in range(bh)]
            if any(v != 0 for row in content for v in row):
                motifs[br] = (bc, content)

    # build the post-transform grid of motif placements
    target = {}  # (br, new_bc) -> content
    for br, (bc, content) in motifs.items():
        new_bc = nbc - 1 - bc
        target[(br, new_bc)] = content

    # T: dict {(r,c): new_color} for every cell, derived from target placement.
    # Start from an all-zero canvas (the blocks fully cover the grid here) and
    # paint the relocated motifs.
    new_vals = [[0] * W for _ in range(H)]
    for (br, bc), content in target.items():
        for a in range(bh):
            for b in range(bw):
                new_vals[br * bh + a][bc * bw + b] = content[a][b]

    T = {}
    for r in range(H):
        for c in range(W):
            if new_vals[r][c] != input_grid[r][c]:
                T[(r, c)] = new_vals[r][c]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
