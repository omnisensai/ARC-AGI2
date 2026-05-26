from collections import Counter


def _detect_layout(g):
    """Find block-grid layout by locating uniform separator rows/cols."""
    H, W = len(g), len(g[0])

    def uniform_row(r):
        return len(set(g[r])) == 1

    def uniform_col(c):
        return len(set(g[r][c] for r in range(H))) == 1

    sep_rows = set(r for r in range(H) if uniform_row(r))
    sep_cols = set(c for c in range(W) if uniform_col(c))

    def spans(sset, N):
        res = []
        r = 0
        while r < N:
            if r in sset:
                r += 1
                continue
            r2 = r
            while r2 < N and r2 not in sset:
                r2 += 1
            res.append((r, r2 - 1))
            r = r2
        return res

    return spans(sep_rows, H), spans(sep_cols, W)


def _block_cells(g, rspans, cspans):
    res = {}
    for bi, (r0, r1) in enumerate(rspans):
        for bj, (c0, c1) in enumerate(cspans):
            res[(bi, bj)] = tuple(
                g[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            )
    return res


def infer_T(input_grid):
    """Latent mask: the set of block positions that should hold the special block.

    Each grid is a block-grid of identical 'default' blocks separated by border
    lines. One distinct 'special' block appears; the cells painted with the
    special color form a small template shape. The special blocks present in the
    input are a subset of that template placed somewhere on the block-grid; the
    output paints the special block at EVERY template position. infer_T finds the
    unique placement offset consistent with the input's special blocks.
    """
    g = input_grid
    rspans, cspans = _detect_layout(g)
    nbr, nbc = len(rspans), len(cspans)
    bcells = _block_cells(g, rspans, cspans)

    default = Counter(bcells.values()).most_common(1)[0][0]
    specials = [v for v in bcells.values() if v != default]
    if not specials:
        return {'rspans': rspans, 'cspans': cspans, 'place': set(), 'block': default}

    special = Counter(specials).most_common(1)[0][0]
    spec_in = set(k for k, v in bcells.items() if v == special)

    bw = cspans[0][1] - cspans[0][0] + 1

    # special color = color present in the special block at positions where it
    # differs from the default block (most frequent such color).
    diffcolors = [special[i] for i in range(len(special)) if special[i] != default[i]]
    sc = Counter(diffcolors).most_common(1)[0][0]
    template = set((i // bw, i % bw) for i in range(len(special)) if special[i] == sc)
    th = max(r for r, c in template) + 1
    tw = max(c for r, c in template) + 1

    chosen = None
    for off_r in range(-th, nbr):
        for off_c in range(-tw, nbc):
            placed = set((off_r + r, off_c + c) for (r, c) in template)
            if all(0 <= br < nbr and 0 <= bc < nbc for (br, bc) in placed):
                if spec_in.issubset(placed):
                    chosen = 'AMBIG' if chosen is not None else placed

    place = spec_in if chosen in (None, 'AMBIG') else chosen
    return {'rspans': rspans, 'cspans': cspans, 'place': place, 'block': special}


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    rspans, cspans, block = T['rspans'], T['cspans'], T['block']
    bw = cspans[0][1] - cspans[0][0] + 1
    for (bi, bj) in T['place']:
        r0, r1 = rspans[bi]
        c0, c1 = cspans[bj]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = block[(r - r0) * bw + (c - c0)]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
