"""Canonical latent-T solver for ARC puzzle d753a70b.

Rule (inferred from input structure alone):
  The grid contains several diamond rings (cells at a fixed Manhattan distance
  from a center).  Each ring belongs to one connected colour.  A ring pulses by
  one step:
    * colour 2 rings contract  (radius - 1),
    * colour 5 rings expand    (radius + 1),
    * every other colour stays unchanged.
  The pulse is concentric about the ring's own centre.  When a ring's centre
  lies exactly on a grid boundary edge, its expansion cannot unfold against the
  wall, so the regrown ring drifts one cell perpendicular to that edge toward
  the grid interior.

infer_T builds a latent mask {(r,c): new_colour} describing exactly which cells
change; apply_T copies the input and overwrites only those cells.
"""


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and (r, c) not in seen:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != col:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append((col, set(cells)))
    return comps


def _ring(cr, cc, k, H, W):
    """Cells at Manhattan distance k from (cr,cc), clipped to the grid."""
    s = set()
    if k == 0:
        if 0 <= cr < H and 0 <= cc < W:
            s.add((cr, cc))
        return s
    for dr in range(-k, k + 1):
        dc = k - abs(dr)
        for sg in ({0} if dc == 0 else {dc, -dc}):
            rr, ccc = cr + dr, cc + sg
            if 0 <= rr < H and 0 <= ccc < W:
                s.add((rr, ccc))
    return s


def _fit_ring(cells, H, W):
    """Smallest-radius diamond ring (clipped to grid) that equals `cells`."""
    if len(cells) == 1:
        (r, c) = next(iter(cells))
        return (r, c, 0)
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    best = None
    for cr in range(min(rs) - 12, max(rs) + 13):
        for cc in range(min(cs) - 12, max(cs) + 13):
            for k in range(1, 16):
                if _ring(cr, cc, k, H, W) == cells:
                    if best is None or k < best[2]:
                        best = (cr, cc, k)
                    break
    return best


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} of cells the pulse changes."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = {}
    for col, cells in _components(input_grid, bg):
        fit = _fit_ring(cells, H, W)
        if fit is None:
            continue
        cr, cc, k = fit
        delta = -1 if col == 2 else (1 if col == 5 else 0)
        new_k = k + delta
        ncr, ncc = cr, cc
        if delta > 0:
            on_row_edge = (cr == 0 or cr == H - 1)
            on_col_edge = (cc == 0 or cc == W - 1)
            if on_row_edge and not on_col_edge:
                ncc = cc + (1 if cc < (W - 1) / 2 else -1)
            elif on_col_edge and not on_row_edge:
                ncr = cr + (1 if cr < (H - 1) / 2 else -1)
        if new_k < 0:
            for cell in cells:
                T[cell] = bg
            continue
        new_cells = _ring(ncr, ncc, new_k, H, W)
        for cell in cells:
            if cell not in new_cells:
                T[cell] = bg
        for cell in new_cells:
            T[cell] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
