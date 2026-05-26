def infer_T(input_grid):
    """Infer the latent transformation mask.

    The marker color forms one or more chevron ("V") shapes whose cells are
    connected along the diagonals. Each chevron has two arms meeting at a
    vertex; the region enclosed between the arms must be filled with color 2.
    For every diagonally-connected component, on each grid row that the
    component touches in two or more columns, the background cells strictly
    between the component's leftmost and rightmost column on that row are the
    interior to fill.

    Returns a dict {(r, c): 2} of cells to overwrite.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    colored = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] != bg
    )

    # diagonal-connected components (each is one chevron)
    seen = set()
    comps = []
    for cell in colored:
        if cell in seen:
            continue
        stack = [cell]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in colored:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                stack.append((r + dr, c + dc))
        comps.append(comp)

    T = {}
    for comp in comps:
        rows = {}
        for (r, c) in comp:
            rows.setdefault(r, []).append(c)
        for r, cs in rows.items():
            if len(cs) < 2:
                continue
            for c in range(min(cs) + 1, max(cs)):
                if (r, c) not in colored:
                    T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
