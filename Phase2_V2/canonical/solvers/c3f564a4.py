"""Canonical solver for ARC puzzle c3f564a4.

The grid is a cyclic anti-diagonal pattern: every cell on a given anti-diagonal
(r+c == const) shares one color, and those colors repeat with some period p in
the diagonal index. Cells valued 0 are corrupted holes. The transformation
repairs the holes by restoring the underlying periodic anti-diagonal pattern,
which is inferred from the non-zero (intact) cells.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    maxd = (H - 1) + (W - 1)

    # Consensus color per anti-diagonal index d = r+c, ignoring corrupted (0) cells.
    diag_counts = [dict() for _ in range(maxd + 1)]
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                d = r + c
                diag_counts[d][v] = diag_counts[d].get(v, 0) + 1

    diag_color = [None] * (maxd + 1)
    for d in range(maxd + 1):
        if diag_counts[d]:
            diag_color[d] = max(diag_counts[d], key=diag_counts[d].get)

    # Smallest period p such that diagonal color is a function of (d mod p),
    # and all p residues are actually observed.
    def period_residues(p):
        res = {}
        for d in range(maxd + 1):
            col = diag_color[d]
            if col is None:
                continue
            k = d % p
            if k in res and res[k] != col:
                return None
            res[k] = col
        return res

    chosen = None
    for p in range(1, maxd + 2):
        res = period_residues(p)
        if res is not None and len(res) == p:
            chosen = (p, res)
            break

    T = [[None] * W for _ in range(H)]
    if chosen is None:
        return T
    p, res = chosen
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                k = (r + c) % p
                if k in res:
                    T[r][c] = res[k]
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
