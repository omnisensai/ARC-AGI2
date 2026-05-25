"""Canonical latent-T solver for ARC puzzle 1acc24af.

Same-size scene with two regions sharing a horizontal ground line:
  * a band of color-1 "boxes" -- U-shaped containers open at the bottom -- each
    enclosing an empty "cavity" of a particular shape (a roofed pocket);
  * several color-5 objects sitting below.

Every color-5 object is recolored to 2 if it "fits" one of the box cavities,
otherwise it is left as 5.  An object fits a cavity C when:
  * the object is a solid rectangle of both sides >= 2: a rigid block can only
    seat in a notch of its exact shape, so it fits iff its shape EQUALS C;
  * the cavity is a single-column slot: only a single-column object slides in,
    and it must contain the slot;
  * otherwise (a non-rectangular object, a 2-D cavity): the object fits if it
    contains the cavity shape in some rotation/reflection as a sub-pattern.

infer_T returns the latent mask {(r,c): 2} of all cells of the matching color-5
objects; apply_T overwrites only those cells.
"""


def _components(H, W, pred):
    """4-connected components of cells satisfying pred(r, c)."""
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if pred(r, c) and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if not pred(rr, cc):
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                out.append(cells)
    return out


def _norm(cells):
    """Normalize a set of cells to a frozenset anchored at the top-left."""
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _variants(shape):
    """All rotations/reflections of a normalized shape (each normalized)."""
    res = set()
    cur = set(shape)
    for _ in range(4):
        cur = {(c, -r) for r, c in cur}            # rotate 90 degrees
        res.add(_norm(cur))
        res.add(_norm({(r, -c) for r, c in cur}))   # plus its reflection
    return res


def _dims(shape):
    rs = [r for r, c in shape]
    cs = [c for r, c in shape]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _is_fat_rect(shape):
    h, w = _dims(shape)
    return h > 1 and w > 1 and len(shape) == h * w


def _is_single_col(shape):
    _, w = _dims(shape)
    return w == 1


def _contains(big, small):
    """Does set `big` contain a translated copy of `small`?"""
    bset = set(big)
    for ar, ac in big:
        if all((ar + sr, ac + sc) in bset for sr, sc in small):
            return True
    return False


def _fits(piece, cavity):
    """Whether a color-5 object `piece` fits the box `cavity` (normalized sets)."""
    if _is_fat_rect(piece):
        return piece == cavity
    if _is_single_col(cavity):
        return _is_single_col(piece) and _contains(piece, cavity)
    return any(_contains(piece, v) for v in _variants(cavity))


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Locate the color-1 band and its vertical extent.
    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    if not ones:
        return {}
    rmin = min(r for r, c in ones)
    rmax = max(r for r, c in ones)

    # Box cavities = empty cells inside the band that are "roofed" (have a 1 above
    # them in the same column): the enclosed space of each U-shaped container.
    def roofed(r, c):
        if input_grid[r][c] != 0 or not (rmin <= r <= rmax):
            return False
        return any(input_grid[rr][c] == 1 for rr in range(rmin, r))

    cavities = [_norm(comp) for comp in _components(H, W, roofed)]

    # Recolor each color-5 object to 2 when it fits some box cavity.
    fives = _components(H, W, lambda r, c: input_grid[r][c] == 5)
    T = {}
    for comp in fives:
        shape = _norm(comp)
        if any(_fits(shape, cav) for cav in cavities):
            for (r, c) in comp:
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
