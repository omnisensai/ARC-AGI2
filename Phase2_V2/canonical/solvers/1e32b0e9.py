def infer_T(input_grid):
    """Infer the latent transformation mask {(r,c): new_color}.

    The grid is a 3x3 array of equal panels separated by full lines/columns
    of a single 'separator' color. Each panel holds a fragment of one common
    shape, always drawn at the same panel-local coordinates. The union of all
    fragments reconstructs the complete template shape. The transformation
    stamps that template into every panel: a template cell that is empty
    (background) becomes the separator color; a cell already holding the shape
    color is left as-is (so it is not part of the mask).
    """
    H, W = len(input_grid), len(input_grid[0])

    # Separator color = the color that fills entire rows / columns.
    seprows = [r for r in range(H) if len(set(input_grid[r])) == 1]
    sep = input_grid[seprows[0]][0]
    sepcols = [c for c in range(W)
               if len(set(input_grid[r][c] for r in range(H))) == 1]

    # Panel bounds (regions between separator lines).
    rb = [-1] + seprows + [H]
    cb = [-1] + sepcols + [W]
    panels = []
    for i in range(len(rb) - 1):
        for j in range(len(cb) - 1):
            r0, r1 = rb[i] + 1, rb[i + 1]
            c0, c1 = cb[j] + 1, cb[j + 1]
            if r1 > r0 and c1 > c0:
                panels.append((r0, r1, c0, c1))

    # Background = 0 (the empty filler). Template = union of fragments in
    # panel-local coordinates; any non-background, non-separator cell counts.
    bg = 0
    template = set()
    for (r0, r1, c0, c1) in panels:
        for r in range(r0, r1):
            for c in range(c0, c1):
                v = input_grid[r][c]
                if v != bg and v != sep:
                    template.add((r - r0, c - c0))

    # Build the mask: stamp the template into every panel. Only empty
    # (background) template cells need overwriting -> they become sep.
    T = {}
    for (r0, r1, c0, c1) in panels:
        for (lr, lc) in template:
            r, c = r0 + lr, c0 + lc
            if r0 <= r < r1 and c0 <= c < c1 and input_grid[r][c] == bg:
                T[(r, c)] = sep
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
