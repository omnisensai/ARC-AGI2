"""Canonical latent-T solver for ARC puzzle 28a6681f.

Rule (gravity-driven water settling, color 1 conserved):
  Each grid holds several "container" shapes drawn in solid colors (the walls /
  terrain) plus a reservoir of the special color 1 (water). The water is poured
  down from the top of its reservoir column and settles under downward gravity:
  every unit falls straight down, and when its descent is blocked it spreads
  sideways along the current surface level to the nearest column where it can
  keep falling, finally resting at the deepest cell it can reach. The total
  number of 1-cells is conserved; the reservoir's surplus cascades over the wall
  rims into the empty pockets of the container shapes.

  infer_T -> simulate the settling from the input ALONE and return the latent
             mask T = {(r,c): 1} of the cells the water finally occupies (every
             original 1 is treated as empty during the simulation).
  apply_T -> copy the input, clear the old water (1 -> 0 background), then paint
             the masked cells with 1.
"""

from collections import deque


def _water_source(grid):
    """Top-left cell of the largest 4-connected component of color 1.

    This identifies the reservoir column the water pours down from.
    """
    H, W = len(grid), len(grid[0])
    seen = set()
    best = None
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 1 and (r, c) not in seen:
                comp = []
                dq = deque([(r, c)])
                while dq:
                    rr, cc = dq.popleft()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != 1:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        dq.append((rr + dr, cc + dc))
                if best is None or len(comp) > len(best):
                    best = comp
    if best is None:
        return None
    return min(best, key=lambda rc: (rc[0], rc[1]))


def infer_T(input_grid):
    """Latent mask of the cells that end up holding water (color 1).

    Derived purely from the input by simulating the gravity settling of the
    conserved water mass. Walls are every non-(0, 1) colored cell.
    """
    H, W = len(input_grid), len(input_grid[0])
    wall = [[input_grid[r][c] not in (0, 1) for c in range(W)] for r in range(H)]
    n_water = sum(v == 1 for row in input_grid for v in row)

    T = {}
    src = _water_source(input_grid)
    if src is None or n_water == 0:
        return T
    _, sc = src

    water = [[False] * W for _ in range(H)]

    def free(r, c):
        return 0 <= r < H and 0 <= c < W and not wall[r][c] and not water[r][c]

    for _ in range(n_water):
        # Enter at the topmost free cell of the source column.
        r = 0
        while r < H and not free(r, sc):
            r += 1
        if r >= H:
            break
        c = sc

        # Fall, then settle.
        while True:
            if free(r + 1, c):
                r += 1
                continue
            # Blocked below: spread sideways at the current surface level and
            # look for the nearest column where the unit can keep falling.
            seen = {(r, c)}
            dq = deque([(r, c)])
            drops = []
            while dq:
                rr, cc = dq.popleft()
                if free(rr + 1, cc):
                    drops.append((rr, cc))
                for dc in (-1, 1):
                    nc = cc + dc
                    if free(r, nc) and (r, nc) not in seen:
                        seen.add((r, nc))
                        dq.append((r, nc))
            if not drops:
                # No further descent possible: rest at the cell nearest the
                # source column within the reachable surface segment.
                r, c = min(seen, key=lambda x: (abs(x[1] - sc), x[1]))
                break
            # Continue falling from the descent column nearest the source.
            nd = min(drops, key=lambda x: (abs(x[1] - sc), x[1]))
            r, c = nd[0] + 1, nd[1]

        water[r][c] = True

    for r in range(H):
        for c in range(W):
            if water[r][c]:
                T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    """Copy the input, clear the old water, and paint the masked cells with 1."""
    out = [[(0 if v == 1 else v) for v in row] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
