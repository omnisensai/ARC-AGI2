from collections import defaultdict


def _components(cells):
    """4-connected components of a set of (r, c) cells."""
    cells = set(cells)
    seen = set()
    out = []
    for s in cells:
        if s in seen:
            continue
        stack = [s]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((r + dr, c + dc))
        out.append(sorted(comp))
    return out


def infer_T(input_grid):
    """Infer the diagonal-ray transformation mask from the input structure.

    Object types found in the input:
      * L-corner (3 cells, one cell with both a horizontal and a vertical
        neighbour): an *emitter*.  It launches a diagonal ray pointing away
        from its two arms.
      * line of 3 (straight H or V): a *mirror/obstacle*.  A vertical line
        reflects the horizontal ray component; a horizontal line reflects the
        vertical component.
      * single dot: a per-colour reflector.  A ray of the dot's colour flips
        its vertical (or horizontal) direction when it passes orthogonally
        adjacent to the dot.

    Rays travel diagonally, bounce off line obstacles, reflect once off their
    own-colour dot, and otherwise exit at the grid border.  The returned mask
    maps changed cells -> colour.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    by_color = defaultdict(list)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v:
                by_color[v].append((r, c))

    emitters = []                  # (corner, (dr, dc), color)
    dots_by_color = defaultdict(list)
    obstacle = {}                  # cell -> 'H' or 'V'

    for col, cells in by_color.items():
        for comp in _components(cells):
            cset = set(comp)
            if len(comp) == 1:
                dots_by_color[col].append(comp[0])
            elif len(comp) == 3:
                corner = None
                for (r, c) in comp:
                    horiz = (r, c - 1) in cset or (r, c + 1) in cset
                    vert = (r - 1, c) in cset or (r + 1, c) in cset
                    if horiz and vert:
                        corner = (r, c)
                if corner is not None:
                    r, c = corner
                    up = (r - 1, c) in cset
                    left = (r, c - 1) in cset
                    # ray points away from the arms
                    dr = 1 if up else -1
                    dc = 1 if left else -1
                    emitters.append((corner, (dr, dc), col))
                else:
                    rows = set(r for r, c in comp)
                    orient = 'H' if len(rows) == 1 else 'V'
                    for x in comp:
                        obstacle[x] = orient

    T = {}

    def trace(start, dr, dc, col, my_dots):
        r, c = start
        dot_done = False
        for _ in range(2 * (H + W) + 10):
            if not dot_done:
                for (dr0, dc0) in my_dots:
                    if dr0 == r and abs(dc0 - c) == 1:
                        dc = -dc
                        dot_done = True
                        break
                    if dc0 == c and abs(dr0 - r) == 1:
                        dr = -dr
                        dot_done = True
                        break
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                return
            if (nr, nc) in obstacle:
                if obstacle[(nr, nc)] == 'V':
                    dc = -dc
                else:
                    dr = -dr
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    return
                if (nr, nc) in obstacle:
                    return
            r, c = nr, nc
            if input_grid[r][c] == 0:
                T[(r, c)] = col

    for corner, (dr, dc), col in emitters:
        trace(corner, dr, dc, col, set(dots_by_color.get(col, [])))

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
