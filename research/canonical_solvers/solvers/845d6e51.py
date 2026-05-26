def _components(cells):
    cells = set(cells)
    seen = set()
    out = []
    for s in cells:
        if s in seen:
            continue
        stack = [s]
        comp = []
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in cells:
                continue
            seen.add(cur)
            comp.append(cur)
            r, c = cur
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((r + dr, c + dc))
        out.append(comp)
    return out


def _normalize(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _variants(shape):
    cur = set(shape)
    res = set()
    for _ in range(4):
        cur = {(c, -r) for r, c in cur}
        res.add(_normalize(cur))
        res.add(_normalize({(r, -c) for r, c in cur}))
    return res


def infer_T(input_grid):
    """Infer a latent recolor mask {(r,c): new_color}.

    Structure: a legend lives above a full horizontal line of 5s. The legend
    holds small colored template shapes (separated by 5 columns). Below the
    line are gray (3) shapes. Each gray shape is recolored to the legend color
    whose template it matches under rotation/reflection. The legend's own
    gray (3) template is the source-color key and is not a recolor target.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Find the horizontal divider row: a row beginning with 5 made only of 0/5
    # with several 5s -- separates legend (above) from the field (below).
    hrow = None
    for r in range(H):
        row = input_grid[r]
        if row[0] == 5 and row.count(5) >= 4 and all(v in (0, 5) for v in row):
            hrow = r
            break

    T = {}
    if hrow is None:
        return T

    # Build legend: group non-zero, non-5 cells above the line by color.
    by_color = {}
    for r in range(hrow):
        for c in range(W):
            v = input_grid[r][c]
            if v not in (0, 5):
                by_color.setdefault(v, []).append((r, c))

    # Legend templates as orientation-invariant variant sets, excluding the
    # gray source color (3).
    legend = {}
    for col, cells in by_color.items():
        if col == 3:
            continue
        legend[col] = _variants(_normalize(cells))

    # Gray shapes below the divider.
    gray = [(r, c) for r in range(hrow + 1, H) for c in range(W)
            if input_grid[r][c] == 3]

    for comp in _components(gray):
        shape = _normalize(comp)
        for col, vs in legend.items():
            if shape in vs:
                for cell in comp:
                    T[cell] = col
                break

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
