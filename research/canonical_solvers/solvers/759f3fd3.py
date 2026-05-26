def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure: the grid contains one full row of 3s and one full column of 3s
    that cross at a center cell, splitting the grid into four quadrants. The
    output paints concentric square rings of 4 around that crossing center:
    a cell becomes 4 iff its Chebyshev distance from the center,
    max(|r-r0|, |c-c0|), is a positive even number. The two 3-lines are kept.
    T is a dict mapping (r, c) -> new color for every cell to overwrite.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Locate the center: intersection of the full 3-row and full 3-column.
    full_rows = [r for r in range(H) if all(input_grid[r][c] == 3 for c in range(W))]
    full_cols = [c for c in range(W) if all(input_grid[r][c] == 3 for r in range(H))]
    if not full_rows or not full_cols:
        return {}
    r0, c0 = full_rows[0], full_cols[0]

    T = {}
    for r in range(H):
        for c in range(W):
            if r == r0 or c == c0:
                # Preserve the dividing 3-lines explicitly.
                T[(r, c)] = 3
            else:
                d = max(abs(r - r0), abs(c - c0))
                T[(r, c)] = 4 if d % 2 == 0 else 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
