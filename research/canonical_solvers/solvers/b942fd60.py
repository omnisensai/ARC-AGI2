"""Canonical latent-T solver for ARC puzzle b942fd60.

Rule (bouncing-beam / mirror-lattice tracing):
  A single seed cell of color 2 sits on the grid border.  It emits a horizontal
  beam to the right.  Colored markers (3, 6, 7, 8) act as mirrors.  When a beam
  reaches a mirror it stops on the cell just before it; that prior cell emits a
  perpendicular "cross" (two beams in the two perpendicular directions).  Each
  beam travels over background cells until it hits another mirror or the grid
  edge, where (at a mirror) it in turn emits a cross, and so on.  Every
  background cell a beam covers is overwritten with color 2; the mirror cells
  themselves are preserved.

  Bookkeeping that keeps the lattice finite and consistent with the data:
    * markers of color 8 and 3 emit a cross only the FIRST time they are hit
      (once per cell, regardless of the incoming beam axis);
    * markers of color 6 and 7 may emit once per incoming axis (horizontal vs
      vertical), so a single mirror can turn both a vertical and a horizontal
      beam;
    * a color-7 marker additionally only emits when the perpendicular cross it
      would create reaches a grid edge in at least one direction; otherwise the
      beam is simply absorbed.

  infer_T returns the latent transformation mask (the set of covered cells);
  apply_T copies the input and paints only those cells.
"""

from collections import deque

MIRRORS = (3, 6, 7, 8)
PAINT = 2


def _seed(grid, H, W):
    for r in range(H):
        for c in range(W):
            if grid[r][c] == PAINT:
                return (r, c)
    return None


def _reaches_edge(grid, r, c, dr, dc, H, W):
    """True if a ray from (r,c) heading (dr,dc) reaches the grid edge without
    first hitting a mirror cell."""
    cr, cc = r + dr, c + dc
    while 0 <= cr < H and 0 <= cc < W:
        if grid[cr][cc] in MIRRORS:
            return False
        cr += dr
        cc += dc
    return True


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    mask = {}

    seed = _seed(input_grid, H, W)
    if seed is None:
        return mask
    sr, sc = seed

    seen = set()      # beam states already expanded: (r, c, dr, dc)
    used = {}         # mirror cell -> set of incoming axes that have emitted
    q = deque()
    q.append((sr, sc, 0, 1))   # initial beam: rightward from the seed

    while q:
        r, c, dr, dc = q.popleft()
        if (r, c, dr, dc) in seen:
            continue
        seen.add((r, c, dr, dc))

        cr, cc = r + dr, c + dc
        while 0 <= cr < H and 0 <= cc < W:
            v = input_grid[cr][cc]
            if v in MIRRORS:
                axis = 'h' if dr == 0 else 'v'
                axes = used.get((cr, cc), set())
                if v in (8, 3):
                    can = len(axes) == 0
                else:
                    can = axis not in axes

                br, bc = cr - dr, cc - dc
                perp = [(1, 0), (-1, 0)] if dr == 0 else [(0, 1), (0, -1)]

                if can and v == 7:
                    if not any(_reaches_edge(input_grid, br, bc, pdr, pdc, H, W)
                               for pdr, pdc in perp):
                        can = False

                used.setdefault((cr, cc), set()).add(axis)
                if can:
                    for pdr, pdc in perp:
                        q.append((br, bc, pdr, pdc))
                break
            # background cell: the beam paints it and continues
            mask[(cr, cc)] = PAINT
            cr += dr
            cc += dc

    return mask


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
