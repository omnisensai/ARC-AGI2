"""Canonical latent-T solver for ARC puzzle e1d2900e.

Rule (magnet/attraction):
  The grid contains 2x2 blocks of color 2 and isolated single cells of color 1.
  Each lone 1 that is "aligned" with a block (shares one of the block's two rows
  or two columns) is attracted to its nearest such block and slides along that
  row/column until it sits directly adjacent to the block (keeping its own
  perpendicular coordinate).

  A 1 stays put when it is in equilibrium: it is Chebyshev-equidistant (king-move
  distance) between two or more blocks AND it is aligned with only a single block.
  In that case the competing pulls cancel and the cell does not move.  1s that are
  not aligned with any block also stay put.

Canonical form:
  infer_T scans the input alone (locating blocks via 2x2 detection, locating 1s,
  computing per-cell distances) and returns a latent transformation mask: a dict
  {(r, c): new_color} listing the cells to overwrite (the vacated source cells set
  to background, and the destination cells set to 1).
  apply_T copies the input and overwrites only the masked cells.
"""


def _find_blocks(grid):
    """Top-left coordinates of every 2x2 block of color 2."""
    H, W = len(grid), len(grid[0])
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (grid[r][c] == 2 and grid[r][c + 1] == 2 and
                    grid[r + 1][c] == 2 and grid[r + 1][c + 1] == 2):
                blocks.append((r, c))
    return blocks


def _find_ones(grid):
    H, W = len(grid), len(grid[0])
    return [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 1]


def _comp_dist(r, c, br, bc):
    """Per-axis gap (0 inside the block span) from cell to block region."""
    dr = 0 if br <= r <= br + 1 else min(abs(r - br), abs(r - (br + 1)))
    dc = 0 if bc <= c <= bc + 1 else min(abs(c - bc), abs(c - (bc + 1)))
    return dr, dc


def _aligned_blocks(r, c, blocks):
    """Blocks the cell shares a row-span or column-span with, as
    (manhattan_dist, (br, bc), orientation)."""
    res = []
    for (br, bc) in blocks:
        if r in (br, br + 1) and c not in (bc, bc + 1):
            dr, dc = _comp_dist(r, c, br, bc)
            res.append((dr + dc, (br, bc), 'row'))
        elif c in (bc, bc + 1) and r not in (br, br + 1):
            dr, dc = _comp_dist(r, c, br, bc)
            res.append((dr + dc, (br, bc), 'col'))
    return sorted(res)


def infer_T(input_grid):
    """Compute the latent transformation mask from the input alone."""
    grid = input_grid
    blocks = _find_blocks(grid)
    ones = _find_ones(grid)

    # Background colour = most common value (used to clear vacated cells).
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    T = {}  # latent mask: {(r, c): new_color}
    for (r, c) in ones:
        aligned = _aligned_blocks(r, c, blocks)
        if not aligned:
            continue  # no block to attract this cell -> stays

        # Equilibrium test: Chebyshev (king-move) distance to every block.
        cheb = sorted(max(_comp_dist(r, c, br, bc)) for (br, bc) in blocks)
        cheb_tie = len(cheb) >= 2 and cheb[0] == cheb[1]
        if cheb_tie and len(aligned) == 1:
            continue  # balanced between two attractors, only one reachable -> stays

        # Slide toward the nearest aligned block, snapping adjacent to it while
        # keeping the cell's own perpendicular coordinate.
        _, (br, bc), orient = aligned[0]
        if orient == 'row':
            tc = bc - 1 if c < bc else bc + 2
            target = (r, tc)
        else:
            tr = br - 1 if r < br else br + 2
            target = (tr, c)

        if target != (r, c):
            T[(r, c)] = bg      # vacate the source cell
            T[target] = 1       # place the 1 adjacent to the block
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
