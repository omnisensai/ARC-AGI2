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


def _components(grid, bg):
    """Return list of (cells, colors-set) for orthogonal connected blobs of
    non-bg cells, grouping by adjacency regardless of colour."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and grid[nr][nc] != bg:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common colour overall.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Identify the two block colours: the two most frequent non-bg colours
    # that actually form the big rectangular block (the largest component).
    comps = _components(input_grid, bg)
    if not comps:
        return {}
    block = max(comps, key=len)
    block_set = set(block)
    r0 = min(r for r, c in block)
    r1 = max(r for r, c in block)
    c0 = min(c for r, c in block)
    c1 = max(c for r, c in block)
    bh = r1 - r0 + 1
    bw = c1 - c0 + 1

    # Colour role counts inside the block bounding box.
    col_count = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            v = input_grid[r][c]
            if v != bg:
                col_count[v] = col_count.get(v, 0) + 1
    block_colors = sorted(col_count, key=lambda v: -col_count[v])
    if len(block_colors) < 2:
        return {}
    M, S = block_colors[0], block_colors[1]

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

    # Markers: all non-bg cells not in the block.
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and (r, c) not in block_set:
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
