from collections import Counter


def find_blocks(density, n):
    """Detect the regular tile bands along one axis from per-line fill density.

    Tile bands are dense (high non-zero count); separator/noise lanes are
    sparse. Threshold the density and keep the grouping that yields equal-size,
    evenly-spaced blocks.
    """
    mx = max(density)
    best = None
    for frac in [x / 100 for x in range(80, 30, -5)]:
        thr = mx * frac
        dense = [i for i in range(n) if density[i] >= thr]
        if not dense:
            continue
        blocks = []
        cur = [dense[0]]
        for x in dense[1:]:
            if x == cur[-1] + 1:
                cur.append(x)
            else:
                blocks.append(cur)
                cur = [x]
        blocks.append(cur)
        sizes = set(len(b) for b in blocks)
        if len(blocks) >= 2 and len(sizes) == 1:
            starts = [b[0] for b in blocks]
            gaps = set(starts[i + 1] - starts[i] for i in range(len(starts) - 1))
            if len(gaps) == 1:
                return blocks
        if len(blocks) == 1:
            best = blocks
    return best


def infer_T(input_grid):
    """Latent mask: clean a noisy periodic tiling.

    The grid is a regular array of identical tiles separated by blank lanes,
    corrupted by per-cell noise inside tiles and scattered noise in the
    background. Recover the canonical tile as the per-cell mode (consensus)
    across all tile instances, then mark every cell that must change: tile
    cells differing from the consensus, and any non-zero background noise.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    rowden = [sum(1 for c in range(W) if g[r][c] != 0) for r in range(H)]
    colden = [sum(1 for r in range(H) if g[r][c] != 0) for c in range(W)]
    rb = find_blocks(rowden, H)
    cb = find_blocks(colden, W)
    th, tw = len(rb[0]), len(cb[0])

    consensus = [[None] * tw for _ in range(th)]
    for i in range(th):
        for j in range(tw):
            cnt = Counter()
            for rblk in rb:
                for cblk in cb:
                    cnt[g[rblk[i]][cblk[j]]] += 1
            consensus[i][j] = cnt.most_common(1)[0][0]

    tilecells = set()
    T = [[None] * W for _ in range(H)]
    for rblk in rb:
        for cblk in cb:
            for i in range(th):
                for j in range(tw):
                    r, c = rblk[i], cblk[j]
                    tilecells.add((r, c))
                    if g[r][c] != consensus[i][j]:
                        T[r][c] = consensus[i][j]
    for r in range(H):
        for c in range(W):
            if (r, c) not in tilecells and g[r][c] != 0:
                T[r][c] = 0
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(input_grid), len(input_grid[0])
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
