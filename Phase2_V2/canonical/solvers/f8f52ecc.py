"""Canonical ARC solver for puzzle f8f52ecc.

Rule (inferred from input structure alone):
  The background color is the most common color.  Color 8 forms wall objects.
  Every other non-background color appears as a set of scattered "dots".  Each
  such color's dots are joined into a single open orthogonal polyline (a chain
  visiting every dot) drawn through background cells, never crossing an 8-wall.
  Among all feasible chains the canonical one minimizes (path length, number of
  turns), with a final lexicographic tie-break for determinism.  Colors with a
  single dot are left unchanged.

  infer_T  -> latent mask {(r, c): new_color} of background cells that become
              part of some color's connecting polyline.
  apply_T  -> copies the input and overwrites only the masked cells.
"""

from itertools import permutations, product


def _line(a, b):
    """Ordered list of cells of the straight axis-aligned segment a..b, or None."""
    if a[0] == b[0]:
        step = 1 if b[1] >= a[1] else -1
        return [(a[0], c) for c in range(a[1], b[1] + step, step)]
    if a[1] == b[1]:
        step = 1 if b[0] >= a[0] else -1
        return [(r, a[1]) for r in range(a[0], b[0] + step, step)]
    return None


def _connect(a, b, walls):
    """Candidate ordered point lists joining a to b (straight or single L-bend),
    excluding any route that touches a wall cell."""
    cands = []
    if a[0] == b[0] or a[1] == b[1]:
        seg = _line(a, b)
        if not (set(seg) & walls):
            cands.append(seg)
        return cands
    for corner in ((a[0], b[1]), (b[0], a[1])):
        seq = _line(a, corner)[:-1] + _line(corner, b)
        if not (set(seq) & walls):
            cands.append(seq)
    return cands


def _count_turns(pts):
    def sgn(x):
        return (x > 0) - (x < 0)

    turns = 0
    for k in range(1, len(pts) - 1):
        d1 = (sgn(pts[k][0] - pts[k - 1][0]), sgn(pts[k][1] - pts[k - 1][1]))
        d2 = (sgn(pts[k + 1][0] - pts[k][0]), sgn(pts[k + 1][1] - pts[k][1]))
        if d1 != d2:
            turns += 1
    return turns


def _best_chain(dots, walls):
    """Among all dot orderings and corner choices, pick the connecting polyline
    minimizing (length, turns, lexicographic cells).  Returns set of cells."""
    dots = list(dots)
    if len(dots) < 2:
        return set(dots)
    best = None
    best_key = None
    for perm in permutations(dots):
        seglists = []
        feasible = True
        for k in range(len(perm) - 1):
            cs = _connect(perm[k], perm[k + 1], walls)
            if not cs:
                feasible = False
                break
            seglists.append(cs)
        if not feasible:
            continue
        for combo in product(*seglists):
            seq = [perm[0]]
            for s in combo:
                seq.extend(s[1:])
            cells = set(seq)
            key = (len(cells), _count_turns(seq), tuple(sorted(cells)))
            if best_key is None or key < best_key:
                best_key = key
                best = cells
    return best if best is not None else set(dots)


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    walls = set()
    color_cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            if v == 8:
                walls.add((r, c))
            else:
                color_cells.setdefault(v, []).append((r, c))

    T = {}
    for color, dots in color_cells.items():
        if len(dots) < 2:
            continue
        chain = _best_chain(dots, walls)
        for (r, c) in chain:
            if input_grid[r][c] == bg:
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
