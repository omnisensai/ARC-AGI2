"""Canonical latent-T solver for ARC puzzle db7260a4.

Rule (inferred from all train+test pairs):
  - A single marker cell of color 1 sits in the top row; it is always removed.
  - The grid contains "container" shapes drawn in color 2: a complete container
    is a U-shape open at the top, i.e. a left vertical wall (col cL), a right
    vertical wall (col cR) spanning the same rows r0..r1, and a bottom bar of 2s
    spanning cols cL..cR at row r1, with the enclosed interior empty.
  - If the marker's column lies within [cL, cR] (inclusive) of some complete
    container, that container's interior is filled with color 1.
  - Otherwise (no complete container catches the marker's column), a full line
    of color 1 is drawn along the bottom edge of the grid (opposite the marker).

The latent transformation T is a dict {(r,c): new_color} of cells to overwrite.
infer_T computes it from the input structure alone; apply_T overwrites only
those masked cells on a copy of the input.
"""


def _find_complete_Us(g):
    """Return maximal top-open U containers as (r0, r1, cL, cR) tuples.

    A complete U has: left wall column cL filled with 2 over rows r0..r1,
    right wall column cR filled with 2 over rows r0..r1, a bottom bar of 2s
    at row r1 across cols cL..cR, and an empty interior (rows r0..r1-1,
    cols cL+1..cR-1). For each (cL, cR) we keep the version with the smallest
    r0 (the tallest / maximal container).
    """
    H, W = len(g), len(g[0])
    cells = {(r, c) for r in range(H) for c in range(W) if g[r][c] == 2}
    best = {}
    for r0 in range(H):
        for r1 in range(r0 + 1, H):
            for cL in range(W):
                for cR in range(cL + 2, W):
                    if not all((r, cL) in cells for r in range(r0, r1 + 1)):
                        continue
                    if not all((r, cR) in cells for r in range(r0, r1 + 1)):
                        continue
                    if not all((r1, c) in cells for c in range(cL, cR + 1)):
                        continue
                    if not all(g[r][c] == 0
                               for r in range(r0, r1)
                               for c in range(cL + 1, cR)):
                        continue
                    key = (cL, cR)
                    if key not in best or r0 < best[key][0]:
                        best[key] = (r0, r1, cL, cR)
    return list(best.values())


def infer_T(input_grid):
    """Infer the latent transformation mask T = {(r, c): new_color}."""
    g = input_grid
    H, W = len(g), len(g[0])

    # Locate the marker (single cell of color 1).
    marker = None
    for r in range(H):
        for c in range(W):
            if g[r][c] == 1:
                marker = (r, c)
                break
        if marker is not None:
            break

    T = {}
    if marker is None:
        return T

    mr, mc = marker
    # The marker is always removed.
    T[(mr, mc)] = 0

    # Choose the complete container whose column span contains the marker col.
    chosen = None
    for (r0, r1, cL, cR) in _find_complete_Us(g):
        if cL <= mc <= cR:
            chosen = (r0, r1, cL, cR)
            break

    if chosen is not None:
        r0, r1, cL, cR = chosen
        # Fill the interior of the container with color 1.
        for r in range(r0, r1):
            for c in range(cL + 1, cR):
                if g[r][c] == 0:
                    T[(r, c)] = 1
    else:
        # No container catches the marker: draw a line on the opposite edge.
        for c in range(W):
            T[(H - 1, c)] = 1

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
