def infer_T(input_grid):
    """Infer overwrite mask. The grid is a row of equal-width square panels
    separated by single-column stripes (color 5). The first panel holds the
    source pattern; the following panels are blank (filled with one color) and
    must be overwritten with rotations of the source: panel 2 = source rotated
    90 clockwise, panel 3 = source rotated 180."""
    H, W = len(input_grid), len(input_grid[0])

    # Separator columns: uniform columns whose color differs from both
    # horizontal neighbours (width-1 stripes). Blank-fill panels are >1 wide,
    # so their uniform columns share color with neighbours and are excluded.
    def col_uniform(c):
        return len(set(input_grid[r][c] for r in range(H))) == 1

    sep_cols = []
    for c in range(W):
        if not col_uniform(c):
            continue
        v = input_grid[0][c]
        left_diff = (c == 0) or (input_grid[0][c - 1] != v)
        right_diff = (c == W - 1) or (input_grid[0][c + 1] != v)
        if left_diff and right_diff:
            sep_cols.append(c)

    # Split columns into panels (maximal runs between separators / borders).
    panels = []
    start = 0
    for c in range(W + 1):
        if c == W or c in sep_cols:
            if start < c:
                panels.append(list(range(start, c)))
            start = c + 1
    if not panels:
        return {}

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
