"""Canonical latent-T solver for ARC puzzle 3345333e.

Rule: A solid rectangular block of one color (3/1/8) sits over part of a
shape of another color (2/6/5). The shape is symmetric across a vertical
axis; the block hides the cells on one side. The transformation erases the
block and reconstructs the hidden half by reflecting the visible shape cells
across the (inferred) vertical symmetry axis. The axis is the unique vertical
mirror line for which reflecting the visible shape lands only on existing
shape cells or inside the block region (never on empty background) while
covering at least one cell of the block.
"""

from collections import Counter


def _cells(grid, color):
    H, W = len(grid), len(grid[0])
    return set((r, c) for r in range(H) for c in range(W) if grid[r][c] == color)


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    """Return a latent transformation mask {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])

    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    nonzero = [k for k in cnt if k != 0]

    # Block = the color whose cells form a fully solid rectangle.
    block = None
    block_cells = set()
    for col in nonzero:
        cc = _cells(input_grid, col)
        r0, r1, c0, c1 = _bbox(cc)
        if (r1 - r0 + 1) * (c1 - c0 + 1) == len(cc):
            block = col
            block_cells = cc
    shape = next(k for k in nonzero if k != block)
    shape_cells = _cells(input_grid, shape)

    # Infer the vertical reflection axis (parametrised by axis2 = 2*center).
    chosen = None
    for axis2 in range(0, 2 * W + 1):
        refl = set((r, axis2 - c) for (r, c) in shape_cells if 0 <= axis2 - c < W)
        in_block = sum(1 for cell in refl if cell in block_cells)
        on_empty = sum(
            1
            for cell in refl
            if cell not in block_cells
            and cell not in shape_cells
            and input_grid[cell[0]][cell[1]] == 0
        )
        if on_empty == 0 and in_block > 0:
            chosen = axis2
            break

    # Build the mask: erase block, keep/add the symmetric shape.
    T = {}
    for (r, c) in block_cells:
        T[(r, c)] = 0
    if chosen is not None:
        for (r, c) in shape_cells:
            T[(r, c)] = shape
            nc = chosen - c
            if 0 <= nc < W:
                T[(r, nc)] = shape
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
