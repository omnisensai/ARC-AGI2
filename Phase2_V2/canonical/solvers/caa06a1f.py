"""Canonical solver for ARC puzzle caa06a1f.

Structure of every input: a doubly-periodic ("tiled") pattern occupies the
top-left region, and a solid mono-color frame fills the remaining bottom rows
and right columns.  The output discards the frame and re-tiles the ENTIRE grid
with the pattern, advanced by one step along the columns (the pattern keeps
marching continuously, so the visible tile is shifted by +1 column).

infer_T derives the latent transformation purely from input structure:
  1. locate the frame (fully mono-color border rows/cols) -> pattern block,
  2. measure the block's vertical/horizontal periods,
  3. build the target color of every cell as block[r % ph][(c + 1) % pw],
  4. record (r,c)->color for every cell whose target differs from the input.
apply_T copies the input and overwrites only those masked cells.
"""


def _find_period(seq):
    """Smallest p such that seq is the period-p repetition seq[i] == seq[i % p]."""
    n = len(seq)
    for p in range(1, n + 1):
        if all(seq[i] == seq[i % p] for i in range(n)):
            return p
    return n


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Frame = leading rows/cols that are entirely a single color.
    mono_rows = [r for r in range(H) if len(set(input_grid[r])) == 1]
    mono_cols = [c for c in range(W)
                 if len(set(input_grid[r][c] for r in range(H))) == 1]
    pr_end = mono_rows[0] if mono_rows else H   # pattern block height
    pc_end = mono_cols[0] if mono_cols else W   # pattern block width

    block = [input_grid[r][:pc_end] for r in range(pr_end)]

    # Periods of the pattern block.
    ph = _find_period([tuple(row) for row in block])      # vertical period
    pw = _find_period(block[0]) if block else W           # horizontal period

    # Target color for each cell: the pattern marched one step along columns.
    T = {}
    for r in range(H):
        for c in range(W):
            val = block[r % ph][(c + 1) % pw]
            if val != input_grid[r][c]:
                T[(r, c)] = val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), val in T.items():
        out[r][c] = val
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
