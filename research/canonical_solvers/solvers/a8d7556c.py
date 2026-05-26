"""Canonical solver for ARC puzzle a8d7556c.

Rule: The grid is a field of 0s and 5s. Find every maximal solid rectangle of
0-cells whose *smaller* side is exactly 2 (i.e. 2xN or Nx2 strips, where the
rectangle cannot be extended by one full row/column in any direction while
remaining solidly 0). Where these candidates overlap (e.g. an L/T shaped 0
blob admits both a 2x3 and a 2x4 reading), greedily keep the larger-area
rectangle. Recolor every cell of the kept rectangles to 2; leave the rest of
the grid untouched.
"""

FILL = 2
ZERO = 0


def _is_solid_zero(grid, r0, c0, r1, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != ZERO:
                return False
    return True


def infer_T(input_grid):
    """Compute the latent change mask: dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])

    # Collect every maximal solid 0-rectangle whose minimum side == 2.
    rects = []
    for r0 in range(H):
        for c0 in range(W):
            if input_grid[r0][c0] != ZERO:
                continue
            for r1 in range(r0, H):
                if input_grid[r1][c0] != ZERO and r1 > r0:
                    pass
                for c1 in range(c0, W):
                    if not _is_solid_zero(input_grid, r0, c0, r1, c1):
                        continue
                    # Maximal: cannot grow by a full row/column in any direction.
                    grow_up = r0 > 0 and _is_solid_zero(input_grid, r0 - 1, c0, r0 - 1, c1)
                    grow_down = r1 < H - 1 and _is_solid_zero(input_grid, r1 + 1, c0, r1 + 1, c1)
                    grow_left = c0 > 0 and _is_solid_zero(input_grid, r0, c0 - 1, r1, c0 - 1)
                    grow_right = c1 < W - 1 and _is_solid_zero(input_grid, r0, c1 + 1, r1, c1 + 1)
                    if grow_up or grow_down or grow_left or grow_right:
                        continue
                    h, w = r1 - r0 + 1, c1 - c0 + 1
                    if min(h, w) == 2:
                        rects.append((h * w, r0, c0, r1, c1))

    # Greedily keep larger-area rectangles, dropping any that overlap one
    # already kept (resolves ambiguous 0-blobs deterministically).
    rects.sort(key=lambda x: -x[0])
    used = set()
    T = {}
    for _, r0, c0, r1, c1 in rects:
        cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        if any(cell in used for cell in cells):
            continue
        for cell in cells:
            used.add(cell)
            T[cell] = FILL
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
