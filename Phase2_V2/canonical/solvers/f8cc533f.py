"""Canonical latent-T solver for ARC puzzle f8cc533f.

Rule (inferred from all train+test pairs):
  - The background is the most common color. Every other color is a separate
    "shape" (a connected blob inside its bounding box).
  - All shapes in a grid are partial / noisy copies of ONE common figure that
    is fully mirror-symmetric both vertically and horizontally (4-fold).
  - We reconstruct that common template by symmetrizing each shape about its
    own bounding-box center (union of the 4 reflections) and taking the union
    across the full-size shapes (the modal/largest bounding box). This recovers
    the complete symmetric figure even when individual copies are corrupted or
    truncated.
  - For every shape we then place that template at the offset that best matches
    the shape's existing cells, and stamp it back in the shape's color.

infer_T returns the latent transformation mask as a dict {(r,c): new_color}.
apply_T copies the input and overwrites only those masked cells.
"""

from collections import Counter


def _colors(grid):
    cnt = Counter()
    for row in grid:
        for v in row:
            cnt[v] += 1
    return cnt


def _cells_of(grid, color):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == color]


def _symmetrize(cells):
    """Union of the 4 mirror reflections of `cells` about its bbox center."""
    r0 = min(r for r, c in cells)
    r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells)
    c1 = max(c for r, c in cells)
    cr2, cc2 = r0 + r1, c0 + c1
    s = set()
    for (r, c) in cells:
        for a in (r, cr2 - r):
            for b in (c, cc2 - c):
                s.add((a, b))
    return s, r0, r1, c0, c1


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    grid = input_grid
    H, W = len(grid), len(grid[0])
    cnt = _colors(grid)
    bg = cnt.most_common(1)[0][0]

    shapes = []
    for color in cnt:
        if color == bg:
            continue
        cells = _cells_of(grid, color)
        if not cells:
            continue
        sym, r0, r1, c0, c1 = _symmetrize(cells)
        shapes.append({
            "color": color,
            "cells": set(cells),
            "sym": sym,
            "r0": r0, "r1": r1, "c0": c0, "c1": c1,
            "h": r1 - r0 + 1, "w": c1 - c0 + 1,
        })

    T = {}
    if not shapes:
        return T

    # Determine the template dimensions: most common bbox size, tie -> largest.
    dim_counts = Counter((s["h"], s["w"]) for s in shapes)
    th, tw = max(dim_counts, key=lambda d: (dim_counts[d], d[0] * d[1]))

    # Build the common template (top-left normalized) as the union of the
    # symmetrized full-size shapes.
    template = set()
    for s in shapes:
        if (s["h"], s["w"]) == (th, tw):
            for (r, c) in s["sym"]:
                template.add((r - s["r0"], c - s["c0"]))
    if not template:
        # Fallback: union of every symmetrized shape, normalized to its bbox.
        for s in shapes:
            for (r, c) in s["sym"]:
                template.add((r - s["r0"], c - s["c0"]))

    # Place the template for each shape at the best-fitting offset.
    for s in shapes:
        color = s["color"]
        cellset = s["cells"]
        r0, c0 = s["r0"], s["c0"]
        best = None
        for dr in range(r0 - 2, r0 + 3):
            for dc in range(c0 - 2, c0 + 3):
                placed = set((tr + dr, tc + dc) for (tr, tc) in template)
                match = len(placed & cellset)
                extra = len(cellset - placed)
                score = (match, -extra, -(abs(dr - r0) + abs(dc - c0)))
                if best is None or score > best[0]:
                    best = (score, placed)
        placed = best[1]

        # Mark removed cells (shape cell not in the template placement) -> bg.
        for (r, c) in cellset:
            if (r, c) not in placed and 0 <= r < H and 0 <= c < W:
                T[(r, c)] = bg
        # Mark added/kept cells -> the shape color.
        for (r, c) in placed:
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = color

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
