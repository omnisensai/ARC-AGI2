"""Canonical latent-T solver for ARC puzzle d94c3b52.

Structure: the grid is partitioned into 3x3 cell blocks separated by a single
0-row / 0-column (block stride 4, blocks anchored at row/col 1). Every block
holds a shape drawn in color 1, except one block which is drawn in color 8 ---
that is the "key" block, and its filled-cell pattern is the key shape.

Transformation:
  * Any block whose 1-pattern exactly equals the key shape is recolored 8
    ("matches"). The key block keeps its 8.
  * The key plus all matching blocks are treated as nodes on the block lattice.
    For every pair of nodes sharing a block-row or block-column, the blocks
    strictly between them (along that straight line) get their filled cells
    recolored to 7.
  * All other blocks are left unchanged.

infer_T returns the latent recolor mask {(r,c): new_color}; apply_T overwrites
only those cells.
"""


def _blocks(g):
    """Return {(block_row, block_col): (anchor_r, anchor_c)} for each 3x3 block."""
    H, W = len(g), len(g[0])
    res = {}
    for br in range(1, H, 4):
        for bc in range(1, W, 4):
            res[(br // 4, bc // 4)] = (br, bc)
    return res


def _pattern(g, ar, ac):
    """Binary fill pattern (1 where non-zero) of the 3x3 block at anchor."""
    return tuple(tuple(1 if g[ar + i][ac + j] else 0 for j in range(3))
                 for i in range(3))


def infer_T(input_grid):
    g = input_grid
    blocks = _blocks(g)

    # Locate the key block: the one drawn in color 8.
    key_idx = None
    for bidx, (ar, ac) in blocks.items():
        if any(g[ar + i][ac + j] == 8 for i in range(3) for j in range(3)):
            key_idx = bidx
            break

    T = {}
    if key_idx is None:
        return T

    key_ar, key_ac = blocks[key_idx]
    key_pat = _pattern(g, key_ar, key_ac)

    # Nodes = key block + blocks whose 1-pattern matches the key shape.
    nodes = set()
    matches = set()
    for bidx, (ar, ac) in blocks.items():
        if bidx == key_idx:
            nodes.add(bidx)
            continue
        if _pattern(g, ar, ac) == key_pat:
            nodes.add(bidx)
            matches.add(bidx)

    # Blocks recolored to 7: those strictly between two collinear nodes.
    sevens = set()
    node_list = list(nodes)
    for i in range(len(node_list)):
        for k in range(i + 1, len(node_list)):
            (r0, c0), (r1, c1) = node_list[i], node_list[k]
            if r0 == r1:
                for c in range(min(c0, c1) + 1, max(c0, c1)):
                    sevens.add((r0, c))
            elif c0 == c1:
                for r in range(min(r0, r1) + 1, max(r0, r1)):
                    sevens.add((r, c0))
    sevens -= nodes

    # Build the pixel-level recolor mask: overwrite only the filled cells.
    def paint(bidx, color):
        ar, ac = blocks[bidx]
        for i in range(3):
            for j in range(3):
                if g[ar + i][ac + j] != 0:
                    T[(ar + i, ac + j)] = color

    for bidx in matches:
        paint(bidx, 8)
    for bidx in sevens:
        paint(bidx, 7)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
