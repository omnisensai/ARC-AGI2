def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(H):
        for sc in range(W):
            if grid[sr][sc] == color and (sr, sc) not in seen:
                stack = [(sr, sc)]
                cells = []
                while stack:
                    r, c = stack.pop()
                    if (r, c) in seen or not (0 <= r < H and 0 <= c < W):
                        continue
                    if grid[r][c] != color:
                        continue
                    seen.add((r, c))
                    cells.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                comps.append(set(cells))
    return comps


def _palette(grid):
    """The marker key: a row (or column) holding >=2 distinct non-background,
    non-shape (non-5) colors. These define the cyclic color sequence used to
    paint the ribbons, ordered as they appear."""
    H, W = len(grid), len(grid[0])
    for r in range(H):
        seg = [grid[r][c] for c in range(W) if grid[r][c] not in (0, 5)]
        if len(seg) >= 2:
            return seg
    for c in range(W):
        seg = [grid[r][c] for r in range(H) if grid[r][c] not in (0, 5)]
        if len(seg) >= 2:
            return seg
    return None


def infer_T(input_grid):
    """Each 5-colored object is a diagonal ribbon with a right-angle 'start'
    corner (the topmost occupied bounding-box corner). Colors fill as nested
    L-shaped bands emanating from that corner:
        band(r,c) = min(distance along the two corner axes)
        color     = palette[band % len(palette)]
    Once a band index exceeds the ribbon's fold depth it clamps, so the deep
    interior becomes a solid band color. Fold depth = bbox_span - (thin_run-1)."""
    palette = _palette(input_grid)
    T = {}
    if not palette:
        return T
    L = len(palette)
    for cells in _components(input_grid, 5):
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        rmin, rmax, cmin, cmax = min(rs), max(rs), min(cs), max(cs)
        # The two thin ends of the ribbon sit on opposite bbox corners.
        corners = [(rmin, cmin), (rmin, cmax), (rmax, cmin), (rmax, cmax)]
        occ = [rc for rc in corners if rc in cells]
        # Start corner = the topmost (then leftmost) occupied corner.
        cr, cc = min(occ, key=lambda rc: (rc[0], rc[1]))
        sr = 1 if cr == rmin else -1
        sc = 1 if cc == cmin else -1
        # Ribbon thickness = narrowest row run (the thin-end / band run width).
        rowcols = {}
        for r, c in cells:
            rowcols.setdefault(r, []).append(c)
        minw = min(len(v) for v in rowcols.values())
        # Bands deeper than this clamp (the ribbon folds back on itself).
        maxband = (cmax - cmin) - (minw - 1)
        for (r, c) in cells:
            band = min(sr * (r - cr), sc * (c - cc))
            if band > maxband:
                band = maxband
            T[(r, c)] = palette[band % L]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
