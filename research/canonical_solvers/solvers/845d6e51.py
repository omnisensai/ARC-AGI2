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

    Structure: a legend box sits in the top-left, closed below by a horizontal
    line of 5s and on the right by a vertical 5 wall. Inside it are small
    colored template shapes. Elsewhere on the grid are gray (3) shapes. Each
    gray shape is recolored to the legend color whose template it matches under
    rotation/reflection. The legend's own gray template (if any) is just the
    source-color key and is not used as a recolor target.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Horizontal divider: a row starting with 5, made only of 0/5, with several
    # 5s -- it closes the legend box from below.
    hrow = None
    for r in range(H):
        row = input_grid[r]
        if row[0] == 5 and row.count(5) >= 4 and all(v in (0, 5) for v in row):
            hrow = r
            break

    T = {}
    if hrow is None:
        return T

    # The divider's leading run of 5s gives the legend box width; its last
    # column is the vertical 5 wall closing the box on the right.
    ext = 0
    for c in range(W):
        if input_grid[hrow][c] == 5:
            ext = c
        else:
            break

    # Legend templates: colored cells inside the box (rows above the divider,
    # columns within its span), grouped by color. The gray source color (3) is
    # excluded as a recolor target.
    by_color = {}
    for r in range(hrow):
        for c in range(ext + 1):
            v = input_grid[r][c]
            if v not in (0, 5):
                by_color.setdefault(v, []).append((r, c))

    legend = {}
    for col, cells in by_color.items():
        if col == 3:
            continue
        legend[col] = _variants(_normalize(cells))

    # Gray (3) field shapes are those outside the legend box.
    box_cells = {(r, c) for r in range(hrow) for c in range(ext + 1)}
    gray = [(r, c) for r in range(H) for c in range(W)
            if input_grid[r][c] == 3 and (r, c) not in box_cells]

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
