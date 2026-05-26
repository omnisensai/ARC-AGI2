"""Canonical solver for ARC puzzle 902510d5.

Rule (same-size grid):
  - The grid contains one large connected diagonal "blob" (the largest 8-connected
    component of non-zero cells), which is preserved unchanged.
  - Every other non-zero cell is a scattered single-cell marker. Exactly one such
    marker sits in an actual grid corner.
  - The single markers that are NOT in the corner are erased. Their COUNT gives the
    leg length N of a right-isosceles triangle, and their most frequent COLOR gives
    the triangle's color.
  - The corner marker is erased and replaced by an N-leg triangle filling that
    corner (cells with Manhattan distance from the corner <= N-1).

Latent T = dict {(r,c): new_color}: 0 to erase markers, tri_color for triangle.
"""

from collections import Counter


def _components(cells):
    """8-connected components over a set of cells."""
    cells = set(cells)
    seen = set()
    comps = []
    for s in cells:
        if s in seen:
            continue
        stack = [s]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        comps.append(comp)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    nonzero = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != 0]

    # Main blob = the largest 8-connected component (kept as-is).
    comps = _components(nonzero)
    blob_set = set(max(comps, key=len)) if comps else set()

    # Markers = every non-zero cell outside the main blob.
    markers = [(r, c) for (r, c) in nonzero if (r, c) not in blob_set]

    corners = {(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)}
    corner_cell = next(((r, c) for (r, c) in markers if (r, c) in corners), None)

    # Single markers (excluding the corner marker): count -> leg, mode color -> color.
    singles = [(r, c) for (r, c) in markers if (r, c) != corner_cell]
    leg = len(singles)
    color_counts = Counter(input_grid[r][c] for (r, c) in singles)
    tri_color = color_counts.most_common(1)[0][0] if color_counts else None

    T = {}
    # Erase all marker cells.
    for (r, c) in markers:
        T[(r, c)] = 0

    # Draw the right triangle of leg `leg` filling the chosen corner.
    if corner_cell is not None and tri_color is not None and leg > 0:
        cr, cc = corner_cell
        for r in range(H):
            for c in range(W):
                if abs(r - cr) + abs(c - cc) <= leg - 1:
                    T[(r, c)] = tri_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
