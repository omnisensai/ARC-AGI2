"""Canonical latent-T solver for ARC puzzle e40b9e2f.

Rule: the grid contains a dense square "core" block plus a few extra marker /
appendage cells.  The output is the 4-fold rotational (C4) closure of the input
about the centre of that core block -- every coloured cell is rotated 0/90/180/
270 degrees about the centre and the resulting positions are filled in.

`infer_T` locates the core centre, computes the C4 orbit of every coloured input
cell, and returns a latent mask `{(r, c): colour}` for the cells that must be
written.  `apply_T` copies the input and overwrites only those masked cells.
"""


def _largest_solid_square_center(grid):
    """Centre (cr, cc) of the largest fully non-zero square block."""
    H, W = len(grid), len(grid[0])
    best = None
    best_size = -1
    for r in range(H):
        for c in range(W):
            s = 0
            while r + s < H and c + s < W:
                ok = True
                for rr in range(r, r + s + 1):
                    if grid[rr][c + s] == 0:
                        ok = False
                        break
                if ok:
                    for cc in range(c, c + s + 1):
                        if grid[r + s][cc] == 0:
                            ok = False
                            break
                if not ok:
                    break
                s += 1
            if s > best_size:
                best_size = s
                best = (r, c, s)
    if best is None:
        return None
    r, c, s = best
    return (r + (s - 1) / 2.0, c + (s - 1) / 2.0)


def _c4_orbit(r, c, cr, cc):
    """Integer grid positions in the 4-fold rotational orbit of (r, c)."""
    dr = r - cr
    dc = c - cc
    offsets = [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)]  # 0, 90, 180, 270
    out = []
    for a, b in offsets:
        rr = cr + a
        cc2 = cc + b
        if abs(rr - round(rr)) < 1e-9 and abs(cc2 - round(cc2)) < 1e-9:
            out.append((int(round(rr)), int(round(cc2))))
    return out


def infer_T(input_grid):
    """Return a latent mask {(r, c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    center = _largest_solid_square_center(input_grid)
    T = {}
    if center is None:
        return T
    cr, cc = center
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0:
                continue
            for rr, ccc in _c4_orbit(r, c, cr, cc):
                if 0 <= rr < H and 0 <= ccc < W:
                    # Existing input colour wins; first writer wins otherwise.
                    if (rr, ccc) not in T:
                        T[(rr, ccc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
