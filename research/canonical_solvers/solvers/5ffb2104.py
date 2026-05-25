"""Canonical solver for ARC puzzle 5ffb2104.

Rule: rigid-body gravity to the right. Each maximal same-color 4-connected
object slides as far right as it can without leaving the grid or overlapping an
already-settled object. Objects nearest the right wall settle first, so trailing
objects pack up flush against them. The transformation mask T records the new
color for every cell of the gravity-packed scene; apply_T overwrites the input
with that mask (clearing original cells, painting the shifted ones).
"""


def _components(grid):
    """Maximal same-color 4-connected non-background components."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x]:
                        continue
                    if grid[y][x] != color:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                comps.append([(y, x, color) for y, x in cells])
    return comps


def infer_T(input_grid):
    """Latent mask: {(r,c): color} for the right-gravity-packed scene."""
    H, W = len(input_grid), len(input_grid[0])
    comps = _components(input_grid)
    # Objects closest to the right wall settle first.
    comps.sort(key=lambda cells: -max(x for _, x, _ in cells))

    occupied = set()
    T = {}
    for cells in comps:
        shift = 0
        while True:
            nxt = shift + 1
            ok = True
            for y, x, _ in cells:
                if x + nxt >= W or (y, x + nxt) in occupied:
                    ok = False
                    break
            if ok:
                shift = nxt
            else:
                break
        for y, x, color in cells:
            occupied.add((y, x + shift))
            T[(y, x + shift)] = color
    return T


def apply_T(input_grid, T):
    """Copy input, clear all non-background cells, then paint the mask."""
    H, W = len(input_grid), len(input_grid[0])
    out = [[0] * W for _ in range(H)]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
