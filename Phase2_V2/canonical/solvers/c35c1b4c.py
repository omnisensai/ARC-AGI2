"""Canonical solver for ARC puzzle c35c1b4c.

Rule: the grid contains a single large blob of one "shape" color sitting on a
noisy background. The intended shape is mirror-symmetric left-to-right about the
grid's vertical center. The transformation completes that symmetry: every cell
whose horizontal mirror belongs to the shape is itself painted the shape color.
Only those newly-added cells change; everything else is left untouched.

infer_T identifies the shape color (the color with the largest 4-connected
component) and builds the latent mask of cells that must become shape-colored.
apply_T copies the input and overwrites only the masked cells.
"""


def _largest_component_color(grid):
    H, W = len(grid), len(grid[0])
    colors = set(v for row in grid for v in row)
    best_color, best_size = None, -1
    for color in colors:
        seen = set()
        for r in range(H):
            for c in range(W):
                if grid[r][c] != color or (r, c) in seen:
                    continue
                stack = [(r, c)]
                size = 0
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W) or grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    size += 1
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                if size > best_size:
                    best_size = size
                    best_color = color
    return best_color


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    shape = _largest_component_color(input_grid)
    T = [[None] * W for _ in range(H)]
    if shape is None:
        return T
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == shape:
                continue
            # mirror cell across the vertical center
            mc = W - 1 - c
            if input_grid[r][mc] == shape:
                T[r][c] = shape
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
