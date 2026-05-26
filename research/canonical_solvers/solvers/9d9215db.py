"""Canonical solver for ARC puzzle 9d9215db.

Rule (same-size 19x19):
  Non-zero cells live on a 9x9 sub-lattice (grid rows/cols 1,3,5,...,17, i.e.
  lattice index = (coord-1)//2). The pattern is a set of concentric square
  rings centered on the lattice center (4,4). Each ring "layer"
  k = min(lr,lc,8-lr,8-lc) is described by ONE corner in the input:
    - a corner seed  -> that ring's 4 corner cells get the seed color
    - an edge seed   -> all of that ring's edge cells get the seed color
  We symmetrize each described corner across the square's dihedral structure
  by filling the whole ring (corners and/or edges) it belongs to.

  T is the latent mask of (row,col)->color over-writes; apply_T copies the
  input and stamps those cells.
"""


def _ring_corners(k):
    return [(k, k), (k, 8 - k), (8 - k, k), (8 - k, 8 - k)]


def _ring_edges(k):
    cells = set()
    lo, hi = k, 8 - k
    if lo == hi:
        return cells
    for c in range(lo, hi + 1):
        cells.add((lo, c))
        cells.add((hi, c))
        cells.add((c, lo))
        cells.add((c, hi))
    for cc in _ring_corners(k):
        cells.discard(cc)
    return cells


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Collect seeds, mapped to the 9x9 lattice (coord -> (coord-1)//2).
    seeds = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and r % 2 == 1 and c % 2 == 1:
                seeds.append(((r - 1) // 2, (c - 1) // 2, v))

    corner_color = {}
    edge_color = {}
    for lr, lc, v in seeds:
        k = min(lr, lc, 8 - lr, 8 - lc)
        if lr in (k, 8 - k) and lc in (k, 8 - k):
            corner_color[k] = v
        else:
            edge_color[k] = v

    # Build the latent mask over full-grid coordinates.
    T = {}
    for k, v in corner_color.items():
        for (a, b) in _ring_corners(k):
            T[(1 + 2 * a, 1 + 2 * b)] = v
    for k, v in edge_color.items():
        for (a, b) in _ring_edges(k):
            T[(1 + 2 * a, 1 + 2 * b)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
