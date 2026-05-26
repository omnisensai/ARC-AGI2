def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid is partitioned into a regular grid of equal-size blocks. Any block
    that contains a marker cell (a non-background cell) is selected to be filled
    with the fill color. The mask records the new color for every cell in each
    selected block.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Marker color = the other (foreground) color, and the fill color = bg+marker
    # consensus. The fill color is the foreground color that emerges in outputs;
    # for this family the markers are one color and blocks are filled with 1.
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    fill = 1

    # Determine block size: largest divisor d>1 of both H and W producing square
    # blocks. ARC grids in this family are 9x9 with 3x3 blocks. Pick block size
    # so the grid splits into a square arrangement of square blocks.
    def divisors(n):
        return [d for d in range(2, n + 1) if n % d == 0]

    bh = bw = None
    # Prefer a block size equal to grid side / number of block rows where the
    # arrangement is square. Try each common divisor; choose the one that gives
    # the most natural partition (block side = sqrt-ish). We pick block side such
    # that grid//side is also an integer for both dims, preferring side==3 style
    # square blocks when H==W.
    if H == W:
        for d in divisors(H):
            if H % d == 0:
                # block side d, number of blocks per side H//d
                bh = bw = d
                # choose the partition where block count per side equals block side
                # (i.e. d such that H//d == d) when possible; else any.
                if H // d == d:
                    bh = bw = d
                    break
        # default fall through keeps last divisor; ensure squareness preference
        chosen = None
        for d in divisors(H):
            if H // d == d:
                chosen = d
                break
        if chosen is not None:
            bh = bw = chosen
        else:
            bh = bw = divisors(H)[0]
    else:
        bh = divisors(H)[0] if divisors(H) else H
        bw = divisors(W)[0] if divisors(W) else W

    nbr, nbc = H // bh, W // bw

    # Which blocks contain a marker.
    selected = set()
    for (r, c) in markers:
        selected.add((r // bh, c // bw))

    T = [[None] * W for _ in range(H)]
    for (br, bc) in selected:
        for r in range(br * bh, br * bh + bh):
            for c in range(bc * bw, bc * bw + bw):
                T[r][c] = fill
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
