"""Canonical solver for ARC puzzle aaef0977.

Rule: a single non-background marker sits on a field of background color.
The output paints every cell with a color chosen by the Manhattan (taxicab)
distance from that marker, cycling through a fixed period-9 color sequence.
The marker cell (distance 0) keeps the marker color, and successive
Manhattan rings step forward through the cycle, wrapping around.
"""

# The fixed cyclic color order radiating out from the marker.
# Any pair's distance->color mapping is a rotation of this single cycle.
CYCLE = [3, 4, 0, 5, 2, 8, 9, 6, 1]


def infer_T(input_grid):
    """Build the latent mask {(r, c): new_color} from the marker alone."""
    H, W = len(input_grid), len(input_grid[0])

    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # the lone marker (any non-background cell)
    marker = next(((r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] != bg), None)
    if marker is None:
        return {}
    mr, mc = marker
    mcol = input_grid[mr][mc]

    # locate the marker color within the cycle so distance 0 == marker color
    start = CYCLE.index(mcol)
    L = len(CYCLE)

    T = {}
    for r in range(H):
        for c in range(W):
            dist = abs(r - mr) + abs(c - mc)
            T[(r, c)] = CYCLE[(start + dist) % L]
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
