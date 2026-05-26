"""Canonical solver for ARC puzzle 103eff5b.

Rule
----
The grid holds two structures:
  * a small "legend": a compact block of single-cell colored markers
    (colors other than 0 background and 8), laid out on a coarse grid where
    some cells are empty (0);
  * a larger "shape" made of 8s, partitioned into a coarse grid of uniform
    square blocks (some block positions present, some empty).

The legend, rotated 90 degrees, is the template for the 8-shape: its coarse
layout (which cells are filled / empty) matches the block layout of the 8-shape,
and the color of each legend cell tells what color the corresponding 8-block
must become. Each 8-block is repainted with that color; everything else is left
untouched.

infer_T computes the recolor mask {(r,c): new_color} for the 8 region;
apply_T copies the input and overwrites only those cells.
"""


def _rot90(m):
    R = len(m)
    return [[m[R - 1 - r][c] for r in range(R)] for c in range(len(m[0]))]


def _legend_grid(g, H, W):
    cells = [(r, c, g[r][c]) for r in range(H) for c in range(W)
             if g[r][c] not in (0, 8)]
    if not cells:
        return None
    rs = [r for r, c, v in cells]
    cs = [c for r, c, v in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    grid = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c, v in cells:
        grid[r - r0][c - c0] = v
    return grid


def _eight_bbox(g, H, W):
    e = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 8]
    if not e:
        return None
    rs = [r for r, c in e]
    cs = [c for r, c in e]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    leg = _legend_grid(input_grid, H, W)
    box = _eight_bbox(input_grid, H, W)
    if leg is None or box is None:
        return T

    # Rotate legend to align its coarse layout with the 8-shape's block grid.
    template = _rot90(leg)
    nr, nc = len(template), len(template[0])

    r0, r1, c0, c1 = box
    Hreg, Wreg = r1 - r0 + 1, c1 - c0 + 1
    if Hreg % nr or Wreg % nc:
        return T
    sh, sw = Hreg // nr, Wreg // nc

    # Recolor each 8-block according to the (rotated) legend color.
    for cr in range(nr):
        for cc in range(nc):
            color = template[cr][cc]
            if color == 0:
                continue
            for dr in range(sh):
                for dc in range(sw):
                    r, c = r0 + cr * sh + dr, c0 + cc * sw + dc
                    if input_grid[r][c] == 8:
                        T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
