def _bands(seps, n):
    """Split indices 0..n-1 into contiguous segments separated by `seps`."""
    segs, cur = [], []
    for i in range(n):
        if i in seps:
            if cur:
                segs.append(cur)
                cur = []
        else:
            cur.append(i)
    if cur:
        segs.append(cur)
    return segs


def infer_T(input_grid):
    """The grid is partitioned by full rows/cols of 5 into a matrix of cells.
    Paint the top-left cell with 1, the center cell with 2, the bottom-right
    cell with 3. Returns a latent mask dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    rsep = set(r for r in range(H) if all(input_grid[r][c] == 5 for c in range(W)))
    csep = set(c for c in range(W) if all(input_grid[r][c] == 5 for r in range(H)))
    rb = _bands(rsep, H)
    cb = _bands(csep, W)
    nr, nc = len(rb), len(cb)
    T = {}
    targets = [((0, 0), 1), ((nr // 2, nc // 2), 2), ((nr - 1, nc - 1), 3)]
    for (bri, bci), color in targets:
        for r in rb[bri]:
            for c in cb[bci]:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
