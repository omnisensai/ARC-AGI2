def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if grid[sr][sc] != color or seen[sr][sc]:
                continue
            stack = [(sr, sc)]
            seen[sr][sc] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def infer_T(input_grid):
    """Infer the latent change mask.

    Structure: one large 'bar' object (the most-cells color forming a single
    connected component) sits in the grid; scattered single-cell dots of two
    'side' colors lie to either side of it (above/below if the bar is
    horizontal, left/right if vertical). For each perpendicular line that has a
    dot on BOTH sides, the dots are pulled in adjacent to the bar and swapped:
    the far-side dot's color is placed just outside the bar on the near side and
    vice-versa. The original dot cells are cleared.

    T is a dict {(r,c): new_color}; cells set to 0 are clearings.
    """
    H, W = len(input_grid), len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Bar color = the non-bg color with the most cells (the dots are sparse).
    nonbg = {k: v for k, v in counts.items() if k != bg}
    T = {}
    if not nonbg:
        return T
    best_color = max(nonbg, key=nonbg.get)

    # The bar is ALL cells of that color (it may be split into several
    # 4-connected pieces, but together they form one band).
    best_cells = [(r, c) for r in range(H) for c in range(W)
                  if input_grid[r][c] == best_color]
    if not best_cells:
        return T

    bar_set = set(best_cells)
    rs = [r for r, c in best_cells]
    cs = [c for r, c in best_cells]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    horizontal = (cmax - cmin) >= (rmax - rmin)

    def is_dot(r, c):
        v = input_grid[r][c]
        return v != bg and v != best_color

    if horizontal:
        # bar spans columns; for each column find bar row-range; dots above/below.
        for c in range(W):
            col_bar = [r for r in range(H) if (r, c) in bar_set]
            if not col_bar:
                continue
            top, bot = min(col_bar), max(col_bar)
            above = [(r, input_grid[r][c]) for r in range(H) if r < top and is_dot(r, c)]
            below = [(r, input_grid[r][c]) for r in range(H) if r > bot and is_dot(r, c)]
            if len(above) == 1 and len(below) == 1:
                ar, acol = above[0]
                br, bcol = below[0]
                T[(ar, c)] = bg
                T[(br, c)] = bg
                if top - 1 >= 0:
                    T[(top - 1, c)] = bcol   # near-top gets far (below) color
                if bot + 1 < H:
                    T[(bot + 1, c)] = acol   # near-bottom gets far (above) color
    else:
        # bar spans rows; for each row find bar col-range; dots left/right.
        for r in range(H):
            row_bar = [c for c in range(W) if (r, c) in bar_set]
            if not row_bar:
                continue
            left, right = min(row_bar), max(row_bar)
            ldots = [(c, input_grid[r][c]) for c in range(W) if c < left and is_dot(r, c)]
            rdots = [(c, input_grid[r][c]) for c in range(W) if c > right and is_dot(r, c)]
            if len(ldots) == 1 and len(rdots) == 1:
                lc, lcol = ldots[0]
                rc, rcol = rdots[0]
                T[(r, lc)] = bg
                T[(r, rc)] = bg
                if left - 1 >= 0:
                    T[(r, left - 1)] = rcol   # near-left gets far (right) color
                if right + 1 < W:
                    T[(r, right + 1)] = lcol  # near-right gets far (left) color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
