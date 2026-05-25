"""Canonical solver for ARC puzzle 13f06aa5.

Rule (same-size):
  The grid is a uniform background containing several 8-cell "arrow" objects.
  Each arrow is a 5-long bar plus a 3-long bar forming an arrowhead, and carries
  exactly one minority-colored "marker" cell. The arrow points along its long
  axis toward the side that holds the marker (the narrow head side):
      - marker above centroid  -> points UP    -> paints the TOP edge
      - marker below centroid  -> points DOWN  -> paints the BOTTOM edge
      - marker left  of centroid -> points LEFT  -> paints the LEFT edge
      - marker right of centroid -> points RIGHT -> paints the RIGHT edge
  For each arrow with marker color M:
      1. paint the whole target edge with M;
      2. shoot a dashed ray of M from the marker toward that edge, painting
         every other cell (marker+2, marker+4, ...) up to the edge.
  Any grid corner shared by two painted edges becomes 0.
  The original arrow objects are left untouched.

Canonical latent-T form: infer_T builds the explicit overwrite mask
{(r,c): color}; apply_T copies the input and writes only the masked cells.
"""

from collections import Counter


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if seen[y][x] or grid[y][x] == bg:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    grid = input_grid
    H, W = len(grid), len(grid[0])
    bg = _background(grid)

    T = {}                 # (r,c) -> color overwrite mask
    edges = {}             # side -> color, for corner resolution

    for cells in _components(grid, bg):
        colors = Counter(grid[y][x] for y, x in cells)
        # marker = the unique minority cell within this object
        markers = [col for col, n in colors.items() if n == 1]
        if not markers:
            continue
        M = markers[0]
        (my, mx) = next((y, x) for y, x in cells if grid[y][x] == M)

        cy = sum(y for y, x in cells) / len(cells)
        cx = sum(x for y, x in cells) / len(cells)

        # pointing direction: marker sits on the head (narrow) side, offset
        # from the centroid along the object's long axis.
        if abs((my - cy)) >= abs((mx - cx)):
            dr = -1 if my < cy else 1
            dc = 0
        else:
            dr = 0
            dc = -1 if mx < cx else 1

        # 1) paint the whole target edge with M
        if dr == -1:
            side = "top"
            for c in range(W):
                T[(0, c)] = M
        elif dr == 1:
            side = "bottom"
            for c in range(W):
                T[(H - 1, c)] = M
        elif dc == -1:
            side = "left"
            for r in range(H):
                T[(r, 0)] = M
        else:
            side = "right"
            for r in range(H):
                T[(r, W - 1)] = M
        edges[side] = M

        # 2) dashed ray from marker toward the edge, every other cell
        ry, rx = my + 2 * dr, mx + 2 * dc
        while 0 <= ry < H and 0 <= rx < W:
            T[(ry, rx)] = M
            ry += 2 * dr
            rx += 2 * dc

    # 3) corners shared by two painted edges become 0
    corner_pairs = {
        (0, 0): ("top", "left"),
        (0, W - 1): ("top", "right"),
        (H - 1, 0): ("bottom", "left"),
        (H - 1, W - 1): ("bottom", "right"),
    }
    for (r, c), (a, b) in corner_pairs.items():
        if a in edges and b in edges:
            T[(r, c)] = 0

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
