"""Canonical solver for ARC puzzle 817e6c09.

Rule
----
The grid is background 0 with several 2x2 squares of color 2 scattered around.
Collect every 2x2 block, sort them in column-major order (by leftmost column,
then by top row), and recolor them in an alternating fashion 2 / 8 such that the
LAST block in that order becomes 8.  Equivalently, a block becomes 8 when its
distance (in count) from the last block is even, and stays 2 otherwise.

infer_T computes the latent mask {(r,c): new_color} of cells to overwrite (only
the blocks that flip to 8). apply_T copies the input and paints those cells.
"""


def _find_blocks(g):
    """Return top-left (r,c) of every 2x2 square of color 2."""
    H, W = len(g), len(g[0])
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (g[r][c] == 2 and g[r][c + 1] == 2
                    and g[r + 1][c] == 2 and g[r + 1][c + 1] == 2):
                blocks.append((r, c))
    return blocks


def infer_T(input_grid):
    """Latent mask: dict {(r,c): 8} of cells that must flip from 2 to 8."""
    blocks = _find_blocks(input_grid)
    # column-major order: leftmost column first, then top row.
    blocks.sort(key=lambda b: (b[1], b[0]))
    N = len(blocks)
    T = {}
    for idx, (r, c) in enumerate(blocks):
        # alternate from the end so the last block becomes 8.
        if (N - 1 - idx) % 2 == 0:
            for rr in (r, r + 1):
                for cc in (c, c + 1):
                    T[(rr, cc)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
