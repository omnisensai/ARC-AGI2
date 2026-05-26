def infer_T(input_grid):
    """Infer overwrite mask. The grid is a row of equal-width square panels
    separated by single-column stripes (color 5). The first panel holds the
    source pattern; the following panels are blank (filled with one color) and
    must be overwritten with rotations of the source: panel 2 = source rotated
    90 clockwise, panel 3 = source rotated 180."""
    H, W = len(input_grid), len(input_grid[0])

    # Find uniform full-height columns and the color of each.
    def col_uniform(c):
        return len(set(input_grid[r][c] for r in range(H))) == 1

    uniform_color = {c: input_grid[0][c] for c in range(W) if col_uniform(c)}

    def split_by(color):
        seps = {c for c, v in uniform_color.items() if v == color}
        panels, start = [], 0
        for c in range(W + 1):
            if c == W or c in seps:
                if start < c:
                    panels.append(list(range(start, c)))
                start = c + 1
        return panels

    # The separator color divides the grid into >=2 equal-width panels.
    best = None
    for color in set(uniform_color.values()):
        panels = split_by(color)
        if len(panels) >= 2 and len({len(p) for p in panels}) == 1:
            # prefer the split with the most panels (finest valid separator)
            if best is None or len(panels) > len(best[1]):
                best = (color, panels)
    if best is None:
        return {}
    panels = best[1]

    src_cols = panels[0]
    n = len(src_cols)
    source = [[input_grid[r][src_cols[ci]] for ci in range(n)]
              for r in range(H)]

    def rot90cw(g):
        return [[g[n - 1 - c][r] for c in range(n)] for r in range(n)]

    def rot180(g):
        return [[g[n - 1 - r][n - 1 - c] for c in range(n)] for r in range(n)]

    transforms = [rot90cw, rot180]
    T = {}
    for idx, cols in enumerate(panels[1:]):
        if idx >= len(transforms) or len(cols) != n:
            continue
        rotated = transforms[idx](source)
        for r in range(H):
            for ci, c in enumerate(cols):
                T[(r, c)] = rotated[r][ci]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
