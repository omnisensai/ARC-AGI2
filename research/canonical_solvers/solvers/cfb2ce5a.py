"""Canonical solver for ARC puzzle cfb2ce5a.

Structure of every pair:
  * A 4x4 (generally R x C) block built from exactly two colours sits in the
    grid.  The more frequent colour is the "main" role M, the second the
    "secondary" role S.
  * Three of the four 2x2 quadrant positions around the block (its own
    position is top-left) are empty and get filled with reflected copies of
    the block:
        top-left      = identity
        top-right     = horizontal flip
        bottom-left   = vertical flip
        bottom-right  = 180 rotation
  * Single-cell markers scattered in the empty quadrant regions tell which
    colours replace roles M / S in each quadrant.  A marker sits at the exact
    cell (inside its quadrant) whose transformed-pattern role it recolours:
    look up that role (M or S) and the marker becomes that role's replacement
    colour for that quadrant.  Any role left unspecified stays background.

infer_T builds a dict {(r,c): new_color} of every cell to overwrite (the three
reflected, recoloured quadrants).  apply_T copies the input and writes them.
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common colour overall.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The block is built from the two most frequent NON-background colours.
    # (Single-cell markers are all other colours, so this separates them even
    # when a marker happens to sit right against the block.)
    non_bg = {v: n for v, n in counts.items() if v != bg}
    if len(non_bg) < 2:
        return {}
    block_colors = sorted(non_bg, key=lambda v: (-non_bg[v], v))
    M, S = block_colors[0], block_colors[1]

    # Block bounding box = bbox of all M / S cells.
    block_set = set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] in (M, S):
                block_set.add((r, c))
    if not block_set:
        return {}
    r0 = min(r for r, c in block_set)
    r1 = max(r for r, c in block_set)
    c0 = min(c for r, c in block_set)
    c1 = max(c for r, c in block_set)
    bh = r1 - r0 + 1
    bw = c1 - c0 + 1

    # Role grid of the original pattern (within the bounding box).
    role = [[None] * bw for _ in range(bh)]
    for r in range(bh):
        for c in range(bw):
            v = input_grid[r0 + r][c0 + c]
            role[r][c] = 'M' if v == M else ('S' if v == S else None)

    def hflip(g):
        return [row[::-1] for row in g]

    def vflip(g):
        return g[::-1]

    def rot180(g):
        return [row[::-1] for row in g[::-1]]

    # The three target quadrants: (top-left row, top-left col, transformed role grid)
    quad_TR = (r0, c1 + 1, hflip(role))
    quad_BL = (r1 + 1, c0, vflip(role))
    quad_BR = (r1 + 1, c1 + 1, rot180(role))
    quadrants = [quad_TR, quad_BL, quad_BR]

    # Markers: every cell whose colour is neither background nor a block colour.
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v not in (bg, M, S):
                markers.append((r, c, v))

    # For each quadrant, figure out which marker colour replaces M and which
    # replaces S.  A marker inside the quadrant's footprint sits on a cell
    # whose transformed role it recolours.
    role_color = {}  # (quad_index, 'M'/'S') -> color
    for qi, (qr0, qc0, g) in enumerate(quadrants):
        for (mr, mc, mv) in markers:
            lr, lc = mr - qr0, mc - qc0
            if 0 <= lr < bh and 0 <= lc < bw:
                rr = g[lr][lc]
                if rr in ('M', 'S'):
                    role_color[(qi, rr)] = mv

    # Build the latent transformation mask (cells to overwrite).
    T = {}
    for qi, (qr0, qc0, g) in enumerate(quadrants):
        for lr in range(bh):
            for lc in range(bw):
                rr = g[lr][lc]
                if rr is None:
                    continue
                col = role_color.get((qi, rr), bg)
                tr, tc = qr0 + lr, qc0 + lc
                if 0 <= tr < H and 0 <= tc < W:
                    T[(tr, tc)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
