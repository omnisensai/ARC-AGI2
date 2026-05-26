"""Canonical latent-T solver for ARC puzzle 3e980e27.

Rule (derived from ALL pairs):
  The grid contains a few small "template" objects and several lone single-cell
  "markers".  A template is a connected component (8-connectivity) made of a
  shape color plus exactly one "center" cell of a distinct color (the center
  color appears exactly once in the component).  A lone marker is a single-cell
  component; its color equals some template's center color.

  Each lone marker is replaced by a stamped copy of the template whose center
  color matches the marker: the template's cells are placed relative to the
  marker (the marker cell taking the role of the template center).

  Orientation: the stamp may be horizontally mirrored.  Within a scene every
  stamp is oriented to share a single "chirality", measured by the sign of the
  shape's row/col covariance (sum over cells of (dr - mean_dr)*(dc - mean_dc)).
  The reference chirality is taken from the template acting as the primary
  marker type (center color 3); other templates are flipped left-right to match
  it.  With no such reference present the canonical sign is negative.

infer_T builds the explicit overwrite mask {(r,c): color}; apply_T paints it.
"""


def _components(grid):
    """8-connected components of all non-zero cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W or seen[y][x] or grid[y][x] == 0:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy or dx:
                                stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def _cov_sign(offsets):
    """Sign of the row/col covariance of a set of (dr, dc) cells (chirality)."""
    n = len(offsets)
    sr = sum(a for a, b in offsets)
    sc = sum(b for a, b in offsets)
    srb = sum(a * b for a, b in offsets)
    v = n * srb - sr * sc  # = n^2 * covariance, integer, same sign as covariance
    return 1 if v > 0 else (-1 if v < 0 else 0)


def infer_T(input_grid):
    """Compute the latent overwrite mask {(r, c): color} from input structure."""
    H, W = len(input_grid), len(input_grid[0])

    templates = {}   # center_color -> list of (dr, dc, color) relative to center
    markers = []     # (r, c, center_color)

    for cells in _components(input_grid):
        colors = {}
        for (r, c) in cells:
            colors.setdefault(input_grid[r][c], []).append((r, c))
        if len(cells) == 1:
            (r, c) = cells[0]
            markers.append((r, c, input_grid[r][c]))
            continue
        # template: the center color is the one occupying exactly one cell
        center_cols = [col for col, pts in colors.items() if len(pts) == 1]
        if not center_cols:
            continue
        cc = center_cols[0]
        cr, ccc = colors[cc][0]
        templates[cc] = [(r - cr, c - ccc, input_grid[r][c]) for (r, c) in cells]

    # Reference chirality for this scene: that of the primary template (center
    # color 3) if present, else the canonical negative sign.
    ref_sign = -1
    for cc, offs in templates.items():
        if cc == 3:
            s = _cov_sign([(dr, dc) for dr, dc, _ in offs])
            if s != 0:
                ref_sign = s

    T = {}
    for (r, c, col) in markers:
        offs = templates.get(col)
        if offs is None:
            continue
        sign = _cov_sign([(dr, dc) for dr, dc, _ in offs])
        use = offs
        if sign != 0 and sign != ref_sign:
            use = [(dr, -dc, tc) for dr, dc, tc in offs]  # horizontal mirror
        for (dr, dc, tc) in use:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = tc
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
