def infer_T(input_grid):
    """Latent mask for a self-similar fractal block grid.

    The grid is tiled into an MxN meta-grid of B-wide square blocks separated by
    single all-zero lines (period B+1). The pattern is self-similar: the block at
    meta-position (bi, bj) is solid foreground except for one hole (0) located at
    intra-block cell (bi, bj). The input only supplies some of those blocks; the
    mask reconstructs every block from this rule.
    """
    H, W = len(input_grid), len(input_grid[0])
    seprows = set(r for r in range(H) if all(input_grid[r][c] == 0 for c in range(W)))
    sepcols = set(c for c in range(W) if all(input_grid[r][c] == 0 for r in range(H)))

    def find_period(n, seps):
        # period p (= block_size+1) must divide n+1, and every line at index
        # k*p-1 must be a separator. The self-similar hole rule requires the meta
        # block count to equal the block size, so prefer a square tiling
        # (block_size == num_blocks); otherwise take the finest valid tiling.
        cands = []
        for p in range(2, n + 1):
            if (n + 1) % p != 0:
                continue
            count = (n + 1) // p
            if all((k * p - 1) in seps for k in range(1, count)):
                cands.append((p - 1, count, p))  # (block_size, num_blocks, period)
        square = [c for c in cands if c[0] == c[1]]
        if square:
            return square[0]
        return min(cands, key=lambda c: c[0])

    bsr, M, perR = find_period(H, seprows)
    bsc, N, perC = find_period(W, sepcols)
    rowstarts = [k * perR for k in range(M)]
    colstarts = [k * perC for k in range(N)]

    # foreground color = most common non-zero color
    cnt = {}
    for row in input_grid:
        for v in row:
            if v != 0:
                cnt[v] = cnt.get(v, 0) + 1
    fg = max(cnt, key=cnt.get) if cnt else 0

    T = [[None] * W for _ in range(H)]
    for bi in range(M):
        r0 = rowstarts[bi]
        for bj in range(N):
            c0 = colstarts[bj]
            for li in range(bsr):
                for lj in range(bsc):
                    r, c = r0 + li, c0 + lj
                    T[r][c] = 0 if (li == bi and lj == bj) else fg
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
