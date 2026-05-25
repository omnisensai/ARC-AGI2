from collections import Counter


def infer_T(input_grid):
    """Latent mask: fill the diagonally-striped interior region.

    The interior (rows >= 3, cols >= 3) is an anti-diagonal stripe pattern:
    every cell on a given anti-diagonal r+c shares one color. A small 2x2 seed
    marker at the top-left corner of the interior is fixed and never recolored.
    Holes (color 0) are damaged cells; we recover each diagonal's true color by
    consensus over the surviving (non-zero, non-seed) cells on that diagonal,
    then mask every interior cell to that diagonal color (skipping the seed).
    """
    H, W = len(input_grid), len(input_grid[0])
    R0, C0 = 3, 3  # top-left of the striped interior
    seed = {(3, 3), (3, 4), (4, 3), (4, 4)}

    # Consensus color per anti-diagonal from surviving interior cells.
    diag = {}
    for r in range(R0, H):
        for c in range(C0, W):
            if (r, c) in seed:
                continue
            v = input_grid[r][c]
            if v == 0:
                continue
            diag.setdefault(r + c, Counter())[v] += 1

    T = [[None] * W for _ in range(H)]
    for r in range(R0, H):
        for c in range(C0, W):
            if (r, c) in seed:
                continue
            cnt = diag.get(r + c)
            if cnt:
                T[r][c] = cnt.most_common(1)[0][0]
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
