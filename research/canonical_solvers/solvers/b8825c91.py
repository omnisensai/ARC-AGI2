"""Canonical solver for ARC puzzle b8825c91.

Rule: every grid is a symmetric mosaic (dihedral / mirror symmetry holds in the
ground-truth output). The input is partially occluded by a rectangular block of
the noise color 4, which breaks the symmetry. Repair: for each occluded cell,
gather the values of its symmetric counterparts (horizontal mirror, vertical
mirror, 180-rotation, and the diagonal transposes when the grid is square) that
are NOT occluded, and take the consensus (majority vote). The transformation
mask T marks exactly the occluded cells and their recovered colors.
"""

NOISE = 4


def _symmetry_maps(H, W):
    """Return symmetric-position functions valid for an HxW grid."""
    maps = [
        lambda r, c: (r, W - 1 - c),          # horizontal mirror
        lambda r, c: (H - 1 - r, c),          # vertical mirror
        lambda r, c: (H - 1 - r, W - 1 - c),  # 180 rotation
    ]
    if H == W:
        maps += [
            lambda r, c: (c, r),              # main-diagonal transpose
            lambda r, c: (W - 1 - c, H - 1 - r),  # anti-diagonal transpose
            lambda r, c: (c, H - 1 - r),      # rot90
            lambda r, c: (W - 1 - c, r),      # rot270
        ]
    return maps


def infer_T(input_grid):
    """Compute the latent repair mask: {(r, c): recovered_color} for noise cells."""
    H, W = len(input_grid), len(input_grid[0])
    maps = _symmetry_maps(H, W)
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != NOISE:
                continue
            votes = {}
            for f in maps:
                rr, cc = f(r, c)
                if 0 <= rr < H and 0 <= cc < W:
                    v = input_grid[rr][cc]
                    if v != NOISE:
                        votes[v] = votes.get(v, 0) + 1
            if votes:
                T[(r, c)] = max(votes, key=lambda k: votes[k])
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked (occluded) cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
