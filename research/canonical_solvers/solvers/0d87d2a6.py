def _components(g):
    """4-connected components of color-2 cells, as lists of (r, c)."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 2 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if not (0 <= a < H and 0 <= b < W) or seen[a][b] or g[a][b] != 2:
                        continue
                    seen[a][b] = True
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def _contains(a_lo, a_hi, b_lo, b_hi):
    """True if interval [a_lo,a_hi] contains [b_lo,b_hi] or vice-versa."""
    return (a_lo >= b_lo and a_hi <= b_hi) or (b_lo >= a_lo and b_hi <= a_hi)


def infer_T(input_grid):
    """Border markers (color 1) define full-grid lines: a top/bottom marker at
    column c draws a vertical line down column c; a left/right marker at row r
    draws a horizontal line across row r. Every line cell becomes color 1.

    A color-2 block that a line passes through is fully recolored to 1.
    Additionally, when a HORIZONTAL line touches a block exactly at the block's
    top or bottom edge, the block re-emits a vertical ray in the direction it
    extends away from that line; that ray recolors the first aligned block it
    reaches (a block whose column span is contained in / contains the source's),
    without drawing a connecting line."""
    H, W = len(input_grid), len(input_grid[0])

    vcols, hrows = set(), set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                if r in (0, H - 1):
                    vcols.add(c)
                if c in (0, W - 1):
                    hrows.add(r)

    blocks = []
    for cells in _components(input_grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        blocks.append({
            'rmin': min(rs), 'rmax': max(rs),
            'cmin': min(cs), 'cmax': max(cs),
            'cells': cells,
        })

    recolor = [False] * len(blocks)
    emissions = []  # (clo, chi, direction, start_row)

    for i, b in enumerate(blocks):
        for hr in hrows:
            if b['rmin'] <= hr <= b['rmax']:
                recolor[i] = True
                if hr == b['rmin']:          # line at top edge -> extend down
                    emissions.append((b['cmin'], b['cmax'], 'DOWN', b['rmax']))
                elif hr == b['rmax']:        # line at bottom edge -> extend up
                    emissions.append((b['cmin'], b['cmax'], 'UP', b['rmin']))
        for vc in vcols:
            if b['cmin'] <= vc <= b['cmax']:
                recolor[i] = True

    for (clo, chi, direction, start) in emissions:
        best, best_d = None, None
        for i, b in enumerate(blocks):
            if recolor[i]:
                continue
            if not _contains(b['cmin'], b['cmax'], clo, chi):
                continue
            if direction == 'UP' and b['rmax'] < start:
                d = start - b['rmax']
            elif direction == 'DOWN' and b['rmin'] > start:
                d = b['rmin'] - start
            else:
                continue
            if best_d is None or d < best_d:
                best_d, best = d, i
        if best is not None:
            recolor[best] = True

    T = {}
    for c in vcols:
        for r in range(H):
            T[(r, c)] = 1
    for r in hrows:
        for c in range(W):
            T[(r, c)] = 1
    for i, b in enumerate(blocks):
        if recolor[i]:
            for (r, c) in b['cells']:
                T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
