def _bands(grid):
    """Split rows into bands separated by fully-background rows."""
    H = len(grid)
    W = len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    bands, cur = [], []
    for r in range(H):
        if all(grid[r][c] == bg for c in range(W)):
            if cur:
                bands.append(cur); cur = []
        else:
            cur.append(r)
    if cur:
        bands.append(cur)
    return bands, bg


def _norm(cells):
    """Normalize a set of (r,c) cells to a top-left-origin frozenset."""
    if not cells:
        return frozenset()
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return frozenset((r - minr, c - minc) for r, c in cells)


def infer_T(input_grid):
    """Infer a {(r,c): color} mask.

    Each band contains a left fixed shape (the 'anchor' color, here 8) and a
    right shape drawn in some unique color. The anchor shape per band, when
    completed into a 5-wide block, leaves a complement region. The color that
    belongs in that complement is the one whose right shape (somewhere in the
    grid) matches the complement's shape exactly. The right shapes are removed
    and the matching color is drawn into each band's complement.
    """
    H = len(input_grid)
    W = len(input_grid[0])
    bands, bg = _bands(input_grid)

    # Determine the anchor color: the non-bg color shared across all bands
    # (appears in every band). Fall back to the globally most common non-bg.
    nonbg_counts = {}
    band_colorsets = []
    for b in bands:
        cset = set()
        for r in b:
            for c in range(W):
                v = input_grid[r][c]
                if v != bg:
                    cset.add(v)
                    nonbg_counts[v] = nonbg_counts.get(v, 0) + 1
        band_colorsets.append(cset)
    anchor = None
    if band_colorsets:
        common = set.intersection(*band_colorsets) if band_colorsets else set()
        if common:
            anchor = max(common, key=lambda v: nonbg_counts[v])
    if anchor is None and nonbg_counts:
        anchor = max(nonbg_counts, key=nonbg_counts.get)

    BW = 5  # block width of the completed left region (cols 0..4)

    band_info = []        # per band: (rows, complement_cells, anchor_cells)
    rightshape_to_color = {}
    for b in bands:
        anchor_cells = set()
        color_cells = set()
        col = None
        for ri, r in enumerate(b):
            for c in range(W):
                v = input_grid[r][c]
                if v == anchor:
                    anchor_cells.add((ri, c))
                elif v != bg:
                    color_cells.add((ri, c))
                    col = v
        # complement: per row, fill cols [#anchor .. BW-1]
        comp = set()
        for ri in range(len(b)):
            cnt = sum(1 for (rr, _) in anchor_cells if rr == ri)
            for cc in range(cnt, BW):
                comp.add((ri, cc))
        band_info.append((b, comp, color_cells))
        if col is not None:
            rightshape_to_color[_norm(color_cells)] = col

    T = {}
    for (b, comp, color_cells) in band_info:
        # clear the original right-side colored shape
        for (ri, c) in color_cells:
            T[(b[ri], c)] = bg
        # find the color whose right shape matches this complement's shape
        key = _norm(comp)
        if key in rightshape_to_color:
            color = rightshape_to_color[key]
            for (ri, c) in comp:
                T[(b[ri], c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
