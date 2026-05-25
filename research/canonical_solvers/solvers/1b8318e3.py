"""Canonical solver for ARC puzzle 1b8318e3.

Rule (same-size grid):
  The grid contains several 2x2 solid blocks of color 5 (these are fixed
  anchors) and a number of scattered single colored cells (any non-zero,
  non-5 color).  Each single cell "snaps" onto the nearest 5-block: it moves
  to the cell of that block's surrounding 4x4 halo (the ring of cells one
  step around the 2x2 block) obtained by clamping the single's (row, col)
  into the halo's bounding box [br-1, br+2] x [bc-1, bc+2].  This keeps an
  aligned coordinate and slides the other one until it is adjacent to the
  block; diagonal singles land on the nearest outside corner.  The 5-blocks
  never move; the single's original cell becomes background.

  When two singles would clamp onto the same halo cell, the closer single
  (by edge-distance to the block) wins and the other is re-assigned to its
  next nearest block.

infer_T builds the latent mask T = {original_single_cell: 0} U
{landing_cell: color}; apply_T copies the input and overwrites masked cells.
"""


def _blocks(g):
    """Return top-left (r,c) of every solid 2x2 block of color 5."""
    H, W = len(g), len(g[0])
    bs = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (g[r][c] == 5 and g[r][c + 1] == 5
                    and g[r + 1][c] == 5 and g[r + 1][c + 1] == 5):
                bs.append((r, c))
    return bs


def _singles(g):
    """Return (r, c, color) for every scattered cell (not background/not 5)."""
    H, W = len(g), len(g[0])
    s = []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v not in (0, 5):
                s.append((r, c, v))
    return s


def _edge_dist(r, c, br, bc):
    """Manhattan distance from (r,c) to the nearest cell of the 2x2 block."""
    nr = min(max(r, br), br + 1)
    nc = min(max(c, bc), bc + 1)
    return abs(r - nr) + abs(c - nc)


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def infer_T(input_grid):
    """Compute the latent transformation mask as {(r, c): new_color}."""
    g = input_grid
    blocks = _blocks(g)
    singles = _singles(g)
    T = {}
    if not blocks:
        return T

    # Clear every original single cell (it moves away).
    for (r, c, _v) in singles:
        T[(r, c)] = 0

    # Place singles closest-to-a-block first so they claim their slot; on a
    # collision the loser falls through to its next nearest block.
    occupied = set()
    order = sorted(
        singles,
        key=lambda s: min(_edge_dist(s[0], s[1], b[0], b[1]) for b in blocks),
    )
    for (r, c, v) in order:
        for (br, bc) in sorted(
            blocks, key=lambda b: _edge_dist(r, c, b[0], b[1])
        ):
            target = (_clamp(r, br - 1, br + 2), _clamp(c, bc - 1, bc + 2))
            if target not in occupied:
                occupied.add(target)
                # Landing cell takes the single's color (may override a 0 we
                # set above if the single barely moves).
                T[target] = v
                break

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
