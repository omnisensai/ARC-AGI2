"""Canonical latent-T solver for ARC puzzle d22278a0.

Rule (inferred from input structure alone):
  - The input is a blank (background 0) grid with a few colored single-cell
    MARKERS sitting at corners of the grid.
  - Each marker emits concentric Chebyshev "L-rings": from the marker's corner,
    using local coordinates (dr, dc) = (|r - mr|, |c - mc|), the ring index of a
    cell is its Chebyshev distance  k = max(dr, dc).
  - A cell is PAINTED with a marker's color iff that marker is the nearest marker
    to the cell (ordinary/Euclidean distance; ties leave the cell untouched) AND
    the Chebyshev distance from the cell to that marker is EVEN. Odd-ring cells
    stay background, producing the nested square-ring (staircase) pattern.

The latent transformation T is a {(r, c): color} mask computed from the marker
geometry. apply_T copies the input and overwrites only masked cells.
"""


def _find_markers(grid):
    """Non-background colored cells are the markers (background = most common)."""
    H, W = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    markers = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg:
                markers.append((r, c, grid[r][c]))
    return markers, bg


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    markers, _bg = _find_markers(input_grid)
    T = {}
    if not markers:
        return T
    for r in range(H):
        for c in range(W):
            # Ownership: nearest marker by Euclidean distance; ties -> no owner.
            best = None
            best_d = None
            tie = False
            for (mr, mc, col) in markers:
                d = (r - mr) ** 2 + (c - mc) ** 2
                if best_d is None or d < best_d:
                    best_d = d
                    best = (mr, mc, col)
                    tie = False
                elif d == best_d:
                    tie = True
            if best is None or tie:
                continue
            mr, mc, col = best
            k = max(abs(r - mr), abs(c - mc))  # Chebyshev ring index
            if k % 2 == 0:
                T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
