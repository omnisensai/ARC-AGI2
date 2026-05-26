"""Solver for ARC puzzle 142ca369.

Structure of every input:
  * L-corners: a 2x2 window holding exactly three same-colored cells (one
    cell empty). Each L-corner is a diagonal EMITTER. It shoots a ray from the
    filled corner diagonally outward, away from the empty corner.
  * Straight lines (>=2 collinear cells), and isolated dots, are MIRRORS. A
    vertical line reflects the horizontal component of a passing diagonal ray
    (flips dx); a horizontal line reflects the vertical component (flips dy).
    A single dot can do either, depending on which side the ray grazes.
    When a ray reflects off a mirror it ALSO takes on the mirror's color.

Rays travel one diagonal cell at a time, recoloring blank cells they pass
through (the original objects are never overwritten). The latent mask T is the
dict of {(r,c): color} for every blank cell a ray paints.
"""


def _find_objects(g):
    """Return (L_corners, mirror_map).

    L_corners: list of (color, sorted-cells) for each 2x2-minus-one shape.
    mirror_map: dict cell -> (color, set_of_orientations) where orientation is
    'V' (vertical line), 'H' (horizontal line) or both (dot).
    """
    H, W = len(g), len(g[0])

    # L-corners detected directly from 2x2 windows (avoids merging two
    # same-colored corners that touch diagonally).
    L_set = set()
    for r in range(H - 1):
        for c in range(W - 1):
            win = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            nz = [g[y][x] for (y, x) in win if g[y][x] != 0]
            if len(nz) == 3 and len(set(nz)) == 1:
                cells = tuple(sorted((y, x) for (y, x) in win if g[y][x] != 0))
                L_set.add((nz[0], cells))

    Lcells = set()
    for _col, cells in L_set:
        Lcells.update(cells)

    mirror = {}
    # Horizontal runs (length >= 2) of one color, excluding L-corner cells.
    for r in range(H):
        c = 0
        while c < W:
            col = g[r][c]
            if col != 0 and (r, c) not in Lcells:
                cc = c
                while cc < W and g[r][cc] == col and (r, cc) not in Lcells:
                    cc += 1
                if cc - c >= 2:
                    for x in range(c, cc):
                        mirror[(r, x)] = (col, {'H'})
                c = cc
            else:
                c += 1
    # Vertical runs (length >= 2).
    for c in range(W):
        r = 0
        while r < H:
            col = g[r][c]
            if col != 0 and (r, c) not in Lcells:
                rr = r
                while rr < H and g[rr][c] == col and (rr, c) not in Lcells:
                    rr += 1
                if rr - r >= 2:
                    for y in range(r, rr):
                        mirror[(y, c)] = (col, {'V'})
                r = rr
            else:
                r += 1
    # Isolated dots act as point mirrors (either axis).
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and (r, c) not in Lcells and (r, c) not in mirror:
                mirror[(r, c)] = (g[r][c], {'V', 'H'})

    return sorted(L_set), mirror


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    L_corners, mirror = _find_objects(g)

    T = {}
    for col, cells in L_corners:
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        r0, c0 = min(rs), min(cs)
        full = {(r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1)}
        (my, mx), = full - set(cells)            # the empty corner
        oy = r0 if my == r0 + 1 else r0 + 1      # opposite (filled) corner
        ox = c0 if mx == c0 + 1 else c0 + 1
        dy, dx = oy - my, ox - mx                # diagonal direction (+-1,+-1)
        y, x = oy + dy, ox + dx                  # first cell beyond the corner
        cur = col

        steps = 0
        while 0 <= y < H and 0 <= x < W and steps < 4 * (H + W):
            steps += 1
            side = mirror.get((y, x + dx))       # vertical mirror to the side
            if side is not None and 'V' in side[1]:
                cur = side[0]
                dx = -dx
            ahead = mirror.get((y + dy, x))      # horizontal mirror ahead
            if ahead is not None and 'H' in ahead[1]:
                cur = ahead[0]
                dy = -dy
            if g[y][x] == 0:
                T[(y, x)] = cur                  # paint blank cell
            y += dy
            x += dx
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
