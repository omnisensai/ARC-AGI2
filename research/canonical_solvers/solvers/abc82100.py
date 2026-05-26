"""Canonical latent-T solver for ARC puzzle abc82100.

Rule (inferred from ALL pairs):
  The grid contains one or more "legend" units plus scattered single-cell
  markers. Each legend unit is a connected blob of color-8 cells (a small
  "stamp" template) together with a 2-cell colored "stack" lying just outside
  the blob, collinear with the blob's centre axis. In that stack the cell
  nearer the blob is the OUTPUT colour and the cell farther away is the MARKER
  colour the unit applies to.

  Transformation:
    * Erase every legend unit (its 8-cells and its 2 stack cells).
    * Each scattered marker is erased and replaced by a copy of its unit's
      8-shape, recoloured to the unit's OUTPUT colour. The copy is anchored so
      that the blob's extreme cell on the stack side (at the centre axis) lands
      exactly on the marker; the shape therefore grows away from the stack.

  This reproduces colour swaps, chevrons, crosses, diamonds and X-shapes seen
  across the pairs with a single mechanism.
"""

DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


def _get_shapes(inp):
    """Connected components (8-connectivity) of color-8 cells."""
    H, W = len(inp), len(inp[0])
    seen = set()
    shapes = []
    for r in range(H):
        for c in range(W):
            if inp[r][c] == 8 and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if inp[rr][cc] != 8:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                shapes.append(comp)
    return shapes


def _find_stack(inp, shape):
    """For one 8-shape, locate its 2-cell colour stack.

    Returns (dir_name, near_cell, far_cell, near_color, far_color) or None.
    The stack sits just outside the shape along its centre axis; the near cell
    touches the shape, the far cell is one step beyond it.
    """
    H, W = len(inp), len(inp[0])
    rs = [r for r, _ in shape]
    cs = [c for _, c in shape]
    cr = (min(rs) + max(rs)) / 2.0
    cc = (min(cs) + max(cs)) / 2.0

    def val(p):
        r, c = p
        return inp[r][c] if 0 <= r < H and 0 <= c < W else None

    for dname, (dr, dc) in DIRS.items():
        if dr != 0:                      # vertical stack -> needs integer centre col
            if cc != int(cc):
                continue
            col = int(cc)
            ext = max(rs) if dr > 0 else min(rs)
            s1 = (ext + dr, col)
            s2 = (ext + 2 * dr, col)
        else:                            # horizontal stack -> needs integer centre row
            if cr != int(cr):
                continue
            row = int(cr)
            ext = max(cs) if dc > 0 else min(cs)
            s1 = (row, ext + dc)
            s2 = (row, ext + 2 * dc)
        v1, v2 = val(s1), val(s2)
        if v1 not in (0, 8, None) and v2 not in (0, 8, None):
            return dname, s1, s2, v1, v2
    return None


def _build_legend(inp):
    """Parse legend units -> {marker_color: (output_color, offsets_from_anchor)}
    plus the set of cells belonging to legends (to be erased)."""
    mapping = {}
    legend_cells = set()
    for shape in _get_shapes(inp):
        info = _find_stack(inp, shape)
        if info is None:
            continue
        dname, s1, s2, near, far = info
        rs = [r for r, _ in shape]
        cs = [c for _, c in shape]
        dr, dc = DIRS[dname]
        # anchor = extreme cell of shape on the stack side, at the centre axis
        if dr != 0:
            anchor = (max(rs) if dr > 0 else min(rs), (min(cs) + max(cs)) // 2)
        else:
            anchor = ((min(rs) + max(rs)) // 2, max(cs) if dc > 0 else min(cs))
        offsets = [(r - anchor[0], c - anchor[1]) for r, c in shape]
        mapping[far] = (near, offsets)
        legend_cells |= set(shape)
        legend_cells.add(s1)
        legend_cells.add(s2)
    return mapping, legend_cells


def infer_T(input_grid):
    """Compute the latent transformation mask as a dict {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    mapping, legend_cells = _build_legend(input_grid)

    T = {}
    # 1. erase every legend cell
    for (r, c) in legend_cells:
        T[(r, c)] = 0
    # 2. stamp each scattered marker
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (0, 8) or (r, c) in legend_cells:
                continue
            if v not in mapping:
                continue
            out_color, offsets = mapping[v]
            T[(r, c)] = 0  # clear the marker itself (may be overwritten below)
            for dr, dc in offsets:
                rr, cc = r + dr, c + dc
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = out_color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the cells named in the mask."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
