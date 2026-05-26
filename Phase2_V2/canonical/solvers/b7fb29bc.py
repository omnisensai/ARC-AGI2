def infer_T(input_grid):
    """Infer the fill mask for the interior of the 3-bordered rectangle.

    A rectangle drawn in color 3 contains an empty interior with a single
    lone marker cell (also color 3) acting as a seed. The interior is filled
    with concentric Chebyshev-distance rings around the seed: rings at odd
    distance become color 4, rings at even distance become color 2. The seed
    cell itself (distance 0) is left unchanged.
    """
    H, W = len(input_grid), len(input_grid[0])
    threes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 3]
    T = {}
    if not threes:
        return T
    rs = [r for r, c in threes]
    cs = [c for r, c in threes]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    # interior is strictly inside the rectangle border
    r0, r1 = rmin + 1, rmax - 1
    c0, c1 = cmin + 1, cmax - 1
    # seed = the lone color-3 cell located inside the interior
    seeds = [(r, c) for r, c in threes if r0 <= r <= r1 and c0 <= c <= c1]
    if not seeds:
        return T
    sr, sc = seeds[0]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) == (sr, sc):
                continue  # keep the seed marker as-is
            cheb = max(abs(r - sr), abs(c - sc))
            T[(r, c)] = 4 if cheb % 2 == 1 else 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
