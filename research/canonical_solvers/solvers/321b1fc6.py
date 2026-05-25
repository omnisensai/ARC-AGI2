def _components(grid, H, W, bg):
    """4-connected components of non-background cells."""
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] != bg:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)
    return comps


def _norm_shape(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    Structure of the puzzle: the grid contains several monochrome color-8
    objects that all share one shape, plus exactly one multi-colored
    'template' object of that same shape (colored with other colors). The
    transformation paints every 8-object with the template's per-cell colors
    (aligned by their bounding-box top-left), and erases the template itself.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    comps = _components(input_grid, H, W, bg)

    # template = the non-pure-8 component
    template = None
    for cells in comps:
        if set(input_grid[r][c] for r, c in cells) != {8}:
            template = cells
            break

    T = {}
    if template is None:
        return T

    tmr = min(r for r, c in template)
    tmc = min(c for r, c in template)
    colormap = {(r - tmr, c - tmc): input_grid[r][c] for r, c in template}
    tshape = frozenset(colormap.keys())

    # erase the template object
    for r, c in template:
        T[(r, c)] = bg

    # recolor every matching 8-shape object by relative position
    for cells in comps:
        if cells is template:
            continue
        if set(input_grid[r][c] for r, c in cells) != {8}:
            continue
        if _norm_shape(cells) != tshape:
            continue
        mr = min(r for r, c in cells)
        mc = min(c for r, c in cells)
        for r, c in cells:
            T[(r, c)] = colormap[(r - mr, c - mc)]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
