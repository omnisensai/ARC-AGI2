"""Canonical solver for ARC puzzle 29ec7d0e.

The grid is a fully P x P periodic color pattern that has been corrupted with
0-cells (noise). The transformation restores the original periodic pattern by:
  1. inferring the smallest tiling period P for which all non-zero cells agree
     at the same (r % P, c % P) residue,
  2. building a consensus tile from the surviving non-zero cells,
  3. overwriting each corrupted (0) cell with its tile value.
"""


def infer_T(input_grid):
    """Infer the repair mask: {(r, c): restored_color} for every 0 cell."""
    H = len(input_grid)
    W = len(input_grid[0])

    def compatible(P):
        seen = {}
        for r in range(H):
            for c in range(W):
                v = input_grid[r][c]
                if v == 0:
                    continue
                key = (r % P, c % P)
                if key in seen and seen[key] != v:
                    return False
                seen[key] = v
        return True

    # Smallest period whose non-zero cells are mutually consistent.
    P = min(H, W)
    for p in range(1, min(H, W) + 1):
        if compatible(p):
            P = p
            break

    # Consensus tile from surviving (non-zero) cells.
    tile = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                tile[(r % P, c % P)] = v

    # Mask: only the corrupted (0) cells get rewritten.
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[(r, c)] = tile.get((r % P, c % P))
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if v is not None:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
