"""Canonical ARC solver for puzzle b25e450b.

Rule (inferred from input structure alone):
  The grid contains rectangular blocks of color 0 sitting in a noisy field of
  background (7) and clutter (5). Each block touches exactly one of the four
  grid edges. Each block slides straight across to the OPPOSITE edge along the
  axis it points (a top-touching block drops to the bottom, a left-touching
  block slides to the right, etc.), keeping its other coordinate fixed.

  As it sweeps, the full strip it travels through (the rows it spans for a
  horizontal move, the columns it spans for a vertical move) is wiped clean:
  every 5 (and the block's vacated 0 cells) become background 7. Then each
  block is re-stamped at the opposite edge.

The latent transformation T is the mask of cells that change: the swept strip
cells (set to 7) and the landing-zone cells (set to 0). apply_T copies the
input and overwrites only those masked cells.
"""


def _components(grid, color):
    """4-connected components of cells equal to `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen:
                        continue
                    if not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] != color:
                        continue
                    seen.add((a, b))
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((a + dr, b + dc))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Return latent mask dict {(r, c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    BLOCK = 0
    BG = 7
    CLUTTER = 5

    sweep_cells = set()   # cells wiped to background
    land_cells = set()    # cells stamped with block color

    for comp in _components(input_grid, BLOCK):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        h = r1 - r0 + 1
        w = c1 - c0 + 1

        touch_top = r0 == 0
        touch_bot = r1 == H - 1
        touch_left = c0 == 0
        touch_right = c1 == W - 1

        if touch_top and not touch_bot:
            # slide down: sweep the columns it spans, land at the bottom
            strip = [(r, col) for r in range(H) for col in range(c0, c1 + 1)]
            nr0, nc0 = H - h, c0
        elif touch_bot and not touch_top:
            # slide up
            strip = [(r, col) for r in range(H) for col in range(c0, c1 + 1)]
            nr0, nc0 = 0, c0
        elif touch_left and not touch_right:
            # slide right: sweep the rows it spans, land at the right
            strip = [(r, col) for r in range(r0, r1 + 1) for col in range(W)]
            nr0, nc0 = r0, W - w
        elif touch_right and not touch_left:
            # slide left
            strip = [(r, col) for r in range(r0, r1 + 1) for col in range(W)]
            nr0, nc0 = r0, 0
        else:
            # block not clearly anchored to one edge: leave it untouched
            continue

        for (r, col) in strip:
            if input_grid[r][col] in (CLUTTER, BLOCK):
                sweep_cells.add((r, col))

        for dr in range(h):
            for dc in range(w):
                land_cells.add((nr0 + dr, nc0 + dc))

    T = {}
    for cell in sweep_cells:
        T[cell] = BG
    # landing cells win over swept cells (a block may slide across another's path)
    for cell in land_cells:
        T[cell] = BLOCK
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
