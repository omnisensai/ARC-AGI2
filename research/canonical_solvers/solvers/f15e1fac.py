"""Canonical latent-T solver for ARC puzzle f15e1fac.

Structure of every pair:
  * A set of 8-markers sits on ONE edge of the grid (all in a single border
    row or column). These are the sources of "beams" that travel straight into
    the grid (away from their edge).
  * A set of 2-markers sits on a PERPENDICULAR edge. Their positions along that
    edge divide the travel direction into consecutive blocks (a new block begins
    AT each 2-marker, measured starting from the 8-edge).
  * Within each block a beam draws a full-block-long segment.  Each block the
    beam steps one cell sideways (along the 2-edge axis) in the direction AWAY
    from the 2-edge.  Cells that step off the grid simply disappear.

infer_T computes the set of cells that should become 8.  apply_T copies the
input and paints exactly those cells.
"""


def _find(grid, color):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == color]


def _edge(cells, H, W):
    """Return (orientation, index) for a set of border cells lying on one edge."""
    rows = {r for r, c in cells}
    cols = {c for r, c in cells}
    if len(rows) == 1:
        r = next(iter(rows))
        return ("top" if r == 0 else "bottom"), r
    if len(cols) == 1:
        c = next(iter(cols))
        return ("left" if c == 0 else "right"), c
    return (None, None)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    eights = _find(input_grid, 8)
    twos = _find(input_grid, 2)

    T = {}
    if not eights or not twos:
        return T

    eight_edge, _ = _edge(eights, H, W)
    two_edge, _ = _edge(twos, H, W)
    if eight_edge is None or two_edge is None:
        return T

    # Travel axis: the axis perpendicular to the 8-edge.
    #   horizontal 8-edge (top/bottom)  -> beams travel vertically (rows)
    #   vertical   8-edge (left/right)  -> beams travel horizontally (cols)
    travel_vertical = eight_edge in ("top", "bottom")

    if travel_vertical:
        # Beams move along rows.  Sources keyed by their column.
        sources = sorted(c for r, c in eights)
        # Travel start row and step.
        if eight_edge == "top":
            start, step, length = 0, 1, H
        else:
            start, step, length = H - 1, -1, H
        # Block boundaries come from 2-marker ROWS.
        markers = sorted(r for r, c in twos)
        lateral_size = W
        # Shift along columns, away from the 2-edge.
        shift = 1 if two_edge == "left" else -1
    else:
        # Beams move along columns.  Sources keyed by their row.
        sources = sorted(r for r, c in eights)
        if eight_edge == "left":
            start, step, length = 0, 1, W
        else:
            start, step, length = W - 1, -1, W
        markers = sorted(c for r, c in twos)
        lateral_size = H
        # Shift along rows, away from the 2-edge.
        shift = 1 if two_edge == "top" else -1

    # Order the travel positions from the 8-edge inward.
    travel_positions = [start + step * i for i in range(length)]

    # Assign a block index to each travel position.  A new block begins AT each
    # marker (measured in travel order from the 8-edge).
    marker_set = set(markers)
    block_of = {}
    blk = 0
    for pos in travel_positions:
        if pos in marker_set:
            blk += 1
        block_of[pos] = blk

    # Paint each beam.
    for s in sources:
        for pos in travel_positions:
            b = block_of[pos]
            lateral = s + shift * b
            if 0 <= lateral < lateral_size:
                if travel_vertical:
                    T[(pos, lateral)] = 8
                else:
                    T[(lateral, pos)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
