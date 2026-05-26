def _components(grid, H, W, colors):
    """8-connected, same-color connected components for the given color set."""
    seen = set()
    comps = []
    nb = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colors and (r, c) not in seen:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != col:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in nb:
                        stack.append((a + dr, b + dc))
                comps.append((col, cells))
    return comps


def _norm(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _orientations(cells):
    """All 8 rotations/reflections of a shape, each normalized to top-left."""
    res = set()
    cur = set(cells)
    res.add(_norm(cur))
    for _ in range(4):
        cur = {(c, -r) for r, c in cur}
        res.add(_norm(cur))
        res.add(_norm({(r, -c) for r, c in cur}))
    return res


def infer_T(input_grid):
    """Infer the latent recolor mask {(r,c): new_color}.

    Structure: a legend box sits in the top region, separated from the field by
    a horizontal line of 5s (and a vertical 5 wall). Inside the box are small
    colored template shapes (colors other than 0/3/5). The field below holds
    gray (3) shapes. Each gray shape is recolored to the legend color whose
    template shape is congruent to it under the dihedral group (rotations and
    reflections). Each gray component is matched independently.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    # Legend templates: any non-background, non-gray, non-separator color.
    legend_colors = set(range(1, 10)) - {3, 5}
    legend = _components(input_grid, H, W, legend_colors)
    leg = {}
    for col, cells in legend:
        leg.setdefault(col, set()).update(_orientations(cells))

    body = _components(input_grid, H, W, {3})

    T = {}
    for _col, cells in body:
        shp = _norm(cells)
        matched = None
        for lc, oris in leg.items():
            if shp in oris:
                matched = lc
                break
        if matched is None:
            continue
        for (r, c) in cells:
            T[(r, c)] = matched
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
