def _background(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(g, bg):
    """8-connected single-color components (the L-trominoes)."""
    H, W = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and (r, c) not in seen:
                col = g[r][c]
                stack = [(r, c)]
                comp = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if g[x][y] != col:
                        continue
                    seen.add((x, y))
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        stack.append((x + dx, y + dy))
                comps.append((col, comp))
    return comps


def _corner_open(pts):
    """Given an L-tromino, return (corner_cell, (dr, dc)) where (dr,dc) is the
    direction in which the two arms extend from the corner cell."""
    s = set(pts)
    for (r, c) in s:
        sr = [p for p in s if p[0] == r and p != (r, c)]   # same-row neighbor (horiz arm)
        sc = [p for p in s if p[1] == c and p != (r, c)]   # same-col neighbor (vert arm)
        if sr and sc:
            return (r, c), (sc[0][0] - r, sr[0][1] - c)
    return None, None


def infer_T(input_grid):
    """Infer the latent mask: for each L-tromino, the corner cell points (opposite
    to its arms) toward one of the four grid corners. Draw a large L hugging that
    grid corner, with arms running along the two grid edges of the tromino's
    quadrant (the half delimited by the central gap row/column)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    mid_r = H // 2
    mid_c = W // 2
    T = {}
    # First erase every original marker cell back to background; the big Ls
    # below will overwrite any cell they reoccupy.
    for col, comp in _components(input_grid, bg):
        if len(comp) != 3:
            continue
        for (r, c) in comp:
            T[(r, c)] = bg
    for col, comp in _components(input_grid, bg):
        if len(comp) != 3:
            continue
        corner, opn = _corner_open(comp)
        if corner is None:
            continue
        dr, dc = opn
        # The corner of the L points opposite to where its arms extend.
        # That determines which grid corner the big L hugs.
        top = (-dr) < 0          # points up -> top half
        left = (-dc) < 0         # points left -> left half
        if top:
            rs = range(0, mid_r)         # vertical arm rows
            home_r = 0
        else:
            rs = range(mid_r + 1, H)
            home_r = H - 1
        if left:
            cs = range(0, mid_c)         # horizontal arm cols
            home_c = 0
        else:
            cs = range(mid_c + 1, W)
            home_c = W - 1
        # vertical arm along the left/right grid edge (home_c column)
        for r in rs:
            T[(r, home_c)] = col
        # horizontal arm along the top/bottom grid edge (home_r row)
        for c in cs:
            T[(home_r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
