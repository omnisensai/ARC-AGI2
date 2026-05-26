"""Canonical solver for ARC puzzle 88207623.

Rule: The grid contains several independent panels. Each panel is a straight
line of color-2 cells (a "mirror" barrier). A connected shape of color-4 cells
sits on one side of the barrier; a single marker pixel (any color not in
{0,2,4}) sits on the opposite side. The transformation reflects the 4-shape
across the barrier and paints the reflected cells with the marker's color.
The input (4-shape, barrier, marker) is preserved; only the reflected cells
are overwritten.
"""


def infer_T(input_grid):
    """Compute the latent mask {(r,c): new_color} of reflected, recolored cells."""
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    # Connected components of color-2 -> each is one barrier line.
    seen = [[False] * W for _ in range(H)]
    bars = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 2 and not seen[r][c]:
                comp = []
                stack = [(r, c)]
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or g[rr][cc] != 2:
                        continue
                    seen[rr][cc] = True
                    comp.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                bars.append(comp)

    T = {}
    for bar in bars:
        rs = [p[0] for p in bar]
        cs = [p[1] for p in bar]
        vertical = len(set(cs)) == 1
        horizontal = len(set(rs)) == 1

        if vertical:
            axis = cs[0]
            rmin, rmax = min(rs), max(rs)
            # Decide which side holds the 4-shape.
            left4 = right4 = 0
            for rr in range(rmin, rmax + 1):
                for cc in range(axis):
                    if g[rr][cc] == 4:
                        left4 += 1
                for cc in range(axis + 1, W):
                    if g[rr][cc] == 4:
                        right4 += 1
            shape_side = 'L' if left4 >= right4 else 'R'
            shape = [
                (rr, cc)
                for rr in range(rmin, rmax + 1)
                for cc in range(W)
                if g[rr][cc] == 4
                and ((shape_side == 'L' and cc < axis) or (shape_side == 'R' and cc > axis))
            ]
            color = _find_marker(g, H, W, bar, axis, vertical, shape_side)
            if color is None:
                continue
            for rr, cc in shape:
                mc = 2 * axis - cc  # reflect column across the barrier
                if 0 <= mc < W:
                    T[(rr, mc)] = color

        elif horizontal:
            axis = rs[0]
            cmin, cmax = min(cs), max(cs)
            up4 = down4 = 0
            for cc in range(cmin, cmax + 1):
                for rr in range(axis):
                    if g[rr][cc] == 4:
                        up4 += 1
                for rr in range(axis + 1, H):
                    if g[rr][cc] == 4:
                        down4 += 1
            shape_side = 'U' if up4 >= down4 else 'D'
            shape = [
                (rr, cc)
                for cc in range(cmin, cmax + 1)
                for rr in range(H)
                if g[rr][cc] == 4
                and ((shape_side == 'U' and rr < axis) or (shape_side == 'D' and rr > axis))
            ]
            color = _find_marker(g, H, W, bar, axis, vertical, shape_side)
            if color is None:
                continue
            for rr, cc in shape:
                mr = 2 * axis - rr  # reflect row across the barrier
                if 0 <= mr < H:
                    T[(mr, cc)] = color
    return T


def _find_marker(g, H, W, bar, axis, vertical, shape_side):
    """Nearest marker pixel (color not in {0,2,4}) on the side opposite the shape."""
    rs = [p[0] for p in bar]
    cs = [p[1] for p in bar]
    best = None
    bestd = None
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v in (0, 2, 4):
                continue
            if vertical:
                opp = (shape_side == 'L' and c > axis) or (shape_side == 'R' and c < axis)
                if not opp:
                    continue
                if not (min(rs) - 2 <= r <= max(rs) + 2):
                    continue
                d = abs(c - axis)
            else:
                opp = (shape_side == 'U' and r > axis) or (shape_side == 'D' and r < axis)
                if not opp:
                    continue
                if not (min(cs) - 2 <= c <= max(cs) + 2):
                    continue
                d = abs(r - axis)
            if bestd is None or d < bestd:
                bestd = d
                best = v
    return best


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
