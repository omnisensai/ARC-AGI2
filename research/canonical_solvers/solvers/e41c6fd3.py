def _components(grid):
    """Return list of monochromatic 4-connected components as dicts."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and (r, c) not in seen:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if (y, x) in seen or not (0 <= y < H and 0 <= x < W):
                        continue
                    if grid[y][x] != col:
                        continue
                    seen.add((y, x))
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((y + dy, x + dx))
                rmin = min(p[0] for p in cells)
                cmin = min(p[1] for p in cells)
                comps.append({"color": col, "cells": cells,
                              "rmin": rmin, "cmin": cmin})
    return comps


def infer_T(input_grid):
    """Latent mask = {(r,c): new_color}.

    Every non-zero shape is moved vertically so that its top row aligns with
    the top row of the anchor shape (the marker shape, color 8). Horizontal
    position is preserved. The anchor stays put. The mask records the cleared
    source cells (-> 0) and the painted destination cells (-> color).
    """
    comps = _components(input_grid)
    if not comps:
        return {}

    # Anchor: the marker shape (color 8). Fall back to the topmost shape.
    anchors = [k for k in comps if k["color"] == 8]
    if anchors:
        anchor_row = anchors[0]["rmin"]
    else:
        anchor_row = min(k["rmin"] for k in comps)

    paint = {}   # destination cells -> color
    sources = set()
    for comp in comps:
        shift = anchor_row - comp["rmin"]
        if shift == 0:
            continue
        for (r, c) in comp["cells"]:
            sources.add((r, c))
            paint[(r + shift, c)] = comp["color"]

    T = {}
    # Clear every source cell that is not reoccupied by a painted destination.
    for (r, c) in sources:
        if (r, c) not in paint:
            T[(r, c)] = 0
    # Paint destinations (override any clears).
    for (r, c), col in paint.items():
        T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), val in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = val
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
