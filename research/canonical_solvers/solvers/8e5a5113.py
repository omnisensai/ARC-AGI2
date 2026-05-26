def infer_T(input_grid):
    """Infer overwrite mask: the two zero-filled 3x3 panels (separated by columns
    of color 5) get rotations of the source panel. Panel 2 = source rotated 90 CW,
    panel 3 = source rotated 180."""
    H, W = len(input_grid), len(input_grid[0])

    # Find separator columns: uniform columns. The separator color is the most
    # common single-value among such columns (distinct from blank-panel fill 0).
    uniform = {c: input_grid[0][c] for c in range(W)
               if len(set(input_grid[r][c] for r in range(H))) == 1}
    if uniform:
        from collections import Counter
        sep_color = Counter(uniform.values()).most_common(1)[0][0]
    else:
        sep_color = None
    sep_cols = [c for c, v in uniform.items() if v == sep_color]
    # Choose the separator color = the value of the most common uniform col value.
    # Identify panels as maximal runs of columns between/around separators.
    panels = []
    start = 0
    for c in range(W + 1):
        if c == W or c in sep_cols:
            if start < c:
                panels.append(list(range(start, c)))
            start = c + 1
    # The first panel is the source; subsequent panels are blank (all zeros) targets.
    if not panels:
        return {}
    src_cols = panels[0]
    source = [[input_grid[r][src_cols[ci]] for ci in range(len(src_cols))]
              for r in range(H)]
    n = len(src_cols)

    def rot90cw(g):
        return [[g[n - 1 - c][r] for c in range(n)] for r in range(n)]

    def rot180(g):
        return [[g[n - 1 - r][n - 1 - c] for c in range(n)] for r in range(n)]

    transforms = [rot90cw, rot180]
    T = {}
    for idx, cols in enumerate(panels[1:]):
        if idx >= len(transforms):
            break
        if len(cols) != n:
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
