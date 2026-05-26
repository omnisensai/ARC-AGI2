"""Canonical latent-T solver for ARC puzzle e8dc4411.

Rule (inferred from all train+test pairs):
  The grid contains a background color, a multi-cell "shape" drawn in one
  non-background color, and a single "marker" cell of a different color.
  The marker sits diagonally off one corner of the shape and indicates a
  diagonal direction.  The shape is stamped repeatedly (recolored to the
  marker color) marching along that diagonal: each copy is the shape
  translated by k*step, where step carries the shape's far corner onto the
  marker.  Stamps continue until they march entirely off the grid.  Only
  cells that were background get painted (the existing shape/marker stay).

Canonical form:
  T = infer_T(input_grid)   -> dict {(r,c): new_color} latent mask
  apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    bg = _background(input_grid)

    # Color frequencies among non-background cells.
    cnt = Counter()
    for row in input_grid:
        for v in row:
            if v != bg:
                cnt[v] += 1

    T = {}
    if not cnt:
        return T

    # Marker = the color that appears exactly once (the rarest non-bg color).
    # Shape  = the other (more frequent) non-bg color.
    ordered = sorted(cnt.items(), key=lambda kv: kv[1])
    marker_color = ordered[0][0]
    if len(ordered) < 2:
        return T
    shape_color = ordered[-1][0]

    marker = None
    shape_cells = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == marker_color and marker is None:
                marker = (r, c)
            elif v == shape_color:
                shape_cells.append((r, c))

    if marker is None or not shape_cells:
        return T

    mr, mc = marker
    rs = [r for r, _ in shape_cells]
    cs = [c for _, c in shape_cells]
    cen_r = (min(rs) + max(rs)) / 2.0
    cen_c = (min(cs) + max(cs)) / 2.0

    # Diagonal direction from the shape toward the marker.
    dr = 1 if mr > cen_r else -1
    dc = 1 if mc > cen_c else -1

    # The shape corner opposite the marker direction (minimizes dr*r + dc*c).
    far = min(shape_cells, key=lambda rc: dr * rc[0] + dc * rc[1])

    # Step vector carries that far corner onto the marker cell.
    vr = mr - far[0]
    vc = mc - far[1]
    if vr == 0 or vc == 0:
        return T  # degenerate; nothing to march

    # March the shape along the diagonal; paint only former-background cells.
    k = 1
    while True:
        rr_all = [r + vr * k for r, _ in shape_cells]
        cc_all = [c + vc * k for _, c in shape_cells]
        for (r, c) in shape_cells:
            nr, nc = r + vr * k, c + vc * k
            if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == bg:
                T[(nr, nc)] = marker_color
        k += 1
        # Stop once an entire stamp lies off the grid.
        if (min(rr_all) >= H or max(rr_all) < 0 or
                min(cc_all) >= W or max(cc_all) < 0 or k > 200):
            break

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
