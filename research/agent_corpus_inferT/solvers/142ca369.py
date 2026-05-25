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

    Object types (4-connected components, classified by shape):
      * L-corner (3 cells, one cell having both an H and a V neighbour) is an
        EMITTER.  It launches a single diagonal ray pointing away from its two
        arms.
      * straight line of 3 (H or V) is a MIRROR.  A vertical line reflects the
        ray's horizontal component, a horizontal line its vertical component.
        When a ray reflects off a mirror, every cell from the reflection point
        onward (until the next reflection) is repainted in the MIRROR's colour.
      * single dot is a per-colour reflector.  A ray of the dot's colour flips
        one velocity component once, the first time it passes orthogonally
        adjacent to that dot.

    A ray steps diagonally from the emitter, recolouring/bouncing on mirrors,
    reflecting once off its own-colour dot, and exits at the grid border (or
    stops if wedged between two mirrors).  The returned mask maps every changed
    empty cell to the colour painted there.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    by_color = defaultdict(list)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v:
                by_color[v].append((r, c))

    emitters = []                 # (corner, (dr, dc), color)
    mirror = {}                   # cell -> ('H' or 'V', color)
    dots_by_color = defaultdict(list)

    for col, cells in by_color.items():
        for comp in _components(cells):
            cset = set(comp)
            if len(comp) == 1:
                dots_by_color[col].append(comp[0])
            elif len(comp) == 3:
                rows = set(r for r, c in comp)
                cols = set(c for r, c in comp)
                if len(rows) == 1:
                    for x in comp:
                        mirror[x] = ('H', col)
                elif len(cols) == 1:
                    for x in comp:
                        mirror[x] = ('V', col)
                else:
                    corner = None
                    for (r, c) in comp:
                        horiz = (r, c - 1) in cset or (r, c + 1) in cset
                        vert = (r - 1, c) in cset or (r + 1, c) in cset
                        if horiz and vert:
                            corner = (r, c)
                    r, c = corner
                    up = (r - 1, c) in cset
                    left = (r, c - 1) in cset
                    dr = 1 if up else -1     # ray points away from the arms
                    dc = 1 if left else -1
                    emitters.append((corner, (dr, dc), col))

    occupied = set()
    for cells in by_color.values():
        for x in cells:
            occupied.add(x)

    T = {}

    def trace(start, dr, dc, color, my_dots):
        r, c = start
        cur = color
        dot_done = False
        for _ in range(4 * (H + W)):
            # one-time reflection off own-colour dot
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
            if (nr, nc) in mirror:
                orient, mcol = mirror[(nr, nc)]
                cur = mcol                     # adopt the mirror's colour
                if (r, c) not in occupied:
                    T[(r, c)] = cur
                if orient == 'V':
                    dc = -dc
                else:
                    dr = -dr
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    return
                if (nr, nc) in mirror:
                    return
                r, c = nr, nc
                if (r, c) not in occupied:
                    T[(r, c)] = cur
                continue
            r, c = nr, nc
            if (r, c) not in occupied:
                T[(r, c)] = cur

    for corner, (dr, dc), color in emitters:
        trace(corner, dr, dc, color, set(dots_by_color.get(color, [])))

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
