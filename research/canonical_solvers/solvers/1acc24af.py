"""Canonical latent-T solver for ARC puzzle 1acc24af.

Rule (same-size grid):
  The grid has two regions on a shared horizontal "ground" line:
    * a connected wall of color 1 forming downward-opening "cups" (boxes that
      enclose empty pockets on three sides: a ceiling above and walls left/right,
      open at the bottom through a gap in the ground line);
    * several separate objects of color 5 sitting below.
  Each cup defines a pocket shape. A color-5 object is recolored to 2 when it
  "matches" some cup:
    * if the pocket is a solid rectangle of both dimensions >= 2, the object
      matches when it contains that rectangle as a solid sub-block (any of the
      8 orientations);
    * otherwise (bars / non-rectangular pockets) the object matches when it can
      be slotted into the cup: in some orientation the object equals the pocket
      plus a tail that hangs straight down through the cup's mouth columns.
  Objects that do not match any cup keep their color.

infer_T computes the latent mask {(r,c): 2} of all cells belonging to matching
color-5 objects; apply_T overwrites only those cells.
"""


def _components(grid, color, diag=True):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nbrs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in seen or not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if grid[cr][cc] != color:
                        continue
                    seen.add((cr, cc))
                    cells.append((cr, cc))
                    for dr, dc in nbrs:
                        stack.append((cr + dr, cc + dc))
                comps.append(cells)
    return comps


def _norm(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _orientations(shape):
    res = set()
    cur = set(_norm(shape))
    for _ in range(4):
        res.add(_norm(cur))
        res.add(_norm(frozenset((r, -c) for r, c in cur)))
        cur = _norm(frozenset((c, -r) for r, c in cur))
    return res


def _cup_pockets(grid):
    """Enclosed empty pockets of the color-1 wall (ceiling + side walls, open below)."""
    ones = _components(grid, 1)
    if not ones:
        return []
    wall = max(ones, key=len)
    top = min(r for r, c in wall)
    bot = max(r for r, c in wall)
    minc = min(c for r, c in wall)
    maxc = max(c for r, c in wall)
    inside = set()
    for r in range(top, bot + 1):
        for c in range(minc, maxc + 1):
            if grid[r][c] != 0:
                continue
            up = any(grid[rr][c] == 1 for rr in range(top, r))
            left = any(grid[r][cc] == 1 for cc in range(minc, c))
            right = any(grid[r][cc] == 1 for cc in range(c + 1, maxc + 1))
            if up and left and right:
                inside.add((r, c))
    seen = set()
    pockets = []
    for cell in list(inside):
        if cell in seen:
            continue
        stack = [cell]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in inside:
                continue
            seen.add(x)
            comp.append(x)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((x[0] + dr, x[1] + dc))
        pockets.append(_norm(comp))
    return pockets


def _is_full_rect(pocket):
    h = max(r for r, c in pocket) + 1
    w = max(c for r, c in pocket) + 1
    return len(pocket) == h * w and h >= 2 and w >= 2


def _contains_block(obj_cells, pocket):
    """Does the object contain the pocket as a solid sub-block (any orientation)?"""
    obj = set(_norm(obj_cells))
    mr = max(r for r, c in obj)
    mc = max(c for r, c in obj)
    for pp in _orientations(pocket):
        pp = set(pp)
        ph = max(r for r, c in pp) + 1
        pw = max(c for r, c in pp) + 1
        for dr in range(0, mr - ph + 2):
            for dc in range(0, mc - pw + 2):
                if all((r + dr, c + dc) in obj for r, c in pp):
                    return True
    return False


def _fits_insert(obj_cells, pocket):
    """Can the object slot into the cup: pocket on top, straight tail through mouth?"""
    pocket = set(pocket)
    ph = max(r for r, c in pocket) + 1
    mouth_row = ph - 1
    mouth = set(c for r, c in pocket if r == mouth_row)
    for oo in _orientations(obj_cells):
        oo = set(oo)
        span = max(c for r, c in oo) + 1
        for dc in range(-span, span + 1):
            shifted = set((r, c + dc) for r, c in oo)
            if not pocket.issubset(shifted):
                continue
            above_ok = all((r, c) in pocket for r, c in shifted if r <= mouth_row)
            below_ok = all(c in mouth for r, c in shifted if r > mouth_row)
            if above_ok and below_ok:
                return True
    return False


def _object_matches(obj_cells, pockets):
    for pocket in pockets:
        if _is_full_rect(pocket):
            if _contains_block(obj_cells, pocket):
                return True
        else:
            if _fits_insert(obj_cells, pocket):
                return True
    return False


def infer_T(input_grid):
    """Latent mask: {(r,c): 2} for every cell of a color-5 object matching a cup."""
    pockets = _cup_pockets(input_grid)
    T = {}
    for obj in _components(input_grid, 5):
        if _object_matches(obj, pockets):
            for (r, c) in obj:
                T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
