"""Canonical latent-T solver for ARC puzzle fe9372f3.

Structure: a plus-shaped marker (color 2, a center cell with one arm in each of
the 4 cardinal directions) sits somewhere on a blank grid. Rays emanate from the
center cell:

  * Along the 4 cardinal axes, beyond the plus arm (distance d >= 2 from the
    center), cells are painted 8, except every third one (d % 3 == 1) which is
    painted 4. This produces the period-3 ...8,8,4,8,8,4... pattern.
  * Along the 4 diagonals, every cell (distance d >= 1) is painted 1.

The plus itself (color 2) is preserved. infer_T computes the dict of changed
cells; apply_T overwrites only those cells.
"""


def _find_plus_center(grid):
    H, W = len(grid), len(grid[0])
    # the center of the plus is the color-2 cell whose 4 cardinal neighbours
    # are also color 2.
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 2:
                continue
            ok = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W) or grid[nr][nc] != 2:
                    ok = False
                    break
            if ok:
                return (r, c)
    return None


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    center = _find_plus_center(input_grid)
    if center is None:
        return T
    cr, cc = center

    # Cardinal axis rays: 8 by default, 4 where distance % 3 == 1, starting at
    # distance 2 (distance 1 is the preserved plus arm).
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d = 2
        while True:
            r, c = cr + dr * d, cc + dc * d
            if not (0 <= r < H and 0 <= c < W):
                break
            T[(r, c)] = 4 if d % 3 == 1 else 8
            d += 1

    # Diagonal rays: color 1 at every distance >= 1.
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        d = 1
        while True:
            r, c = cr + dr * d, cc + dc * d
            if not (0 <= r < H and 0 <= c < W):
                break
            T[(r, c)] = 1
            d += 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
