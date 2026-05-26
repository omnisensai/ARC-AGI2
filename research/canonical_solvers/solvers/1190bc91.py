"""Canonical solver for ARC puzzle 1190bc91.

Rule (discovered from all train+test pairs):

The input contains:
  * one MAIN RAY: the longest connected colored line (>=3 cells of distinct
    colors), pointing to a grid edge (its "tip"), and
  * zero or more DOUBLE markers: 2-cell connected components of a single color
    (one may sit on the top edge, one on a side edge).

After rotating so the main ray is vertical with its tip at the bottom edge:
  1. Each ray cell emits a downward-opening "V" (chevron): cell (r,c) takes the
     ray color whose spine row is (r - |c - spine_col|).  This paints the whole
     lower cone, the colors nesting outward from the tip.
  2. The two ray cells farthest from the tip ALSO emit upward arms (so they form
     a full diagonal X), giving the upper boundary of the central diamond.
  3. Each double marker FLOODS its enclosing wedge (4-connected fill through the
     still-empty cells, blocked by the painted ray cells) with its color.  The
     wedge that has no marker stays background (0).

The transformation mask T overwrites only the cells the construction paints.
"""

from collections import deque


def _rot90(g):
    H = len(g)
    return [[g[H - 1 - c][r] for c in range(H)] for r in range(len(g[0]))]


def _rotk(g, k):
    for _ in range(k % 4):
        g = _rot90(g)
    return g


def _components(g):
    """4-connected components of non-zero cells; returns (list_of_cell_lists, pos_dict)."""
    H, W = len(g), len(g[0])
    pos = {(r, c): g[r][c] for r in range(H) for c in range(W) if g[r][c] != 0}
    used, comps = set(), []
    for cell in pos:
        if cell in used:
            continue
        stack, comp = [cell], []
        while stack:
            x = stack.pop()
            if x in comp or x not in pos:
                continue
            comp.append(x)
            r, c = x
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in pos:
                    stack.append((r + dr, c + dc))
        used.update(comp)
        comps.append(sorted(comp))
    return comps, pos


def _canon_rotation(g):
    """Rotation count k (CW quarter-turns) that puts the main ray vertical, tip at bottom."""
    comps, _ = _components(g)
    main = max(comps, key=len)
    rows = {r for r, c in main}
    cols = {c for r, c in main}
    H, W = len(g), len(g[0])
    if len(cols) == 1:          # already vertical
        if max(rows) == H - 1:
            return 0            # tip at bottom
        if min(rows) == 0:
            return 2            # tip at top -> 180
    if len(rows) == 1:          # horizontal
        if max(cols) == W - 1:
            return 1            # tip at right -> CW once -> bottom
        if min(cols) == 0:
            return 3            # tip at left -> CW thrice -> bottom
    return 0


def infer_T(input_grid):
    """Infer the latent transformation mask T (None / color grid) from the input alone."""
    k = _canon_rotation(input_grid)
    cg = _rotk(input_grid, k)
    H, W = len(cg), len(cg[0])
    comps, pos = _components(cg)

    main = max(comps, key=len)
    spine_col = main[0][1]
    rows = sorted(r for r, c in main)
    ray_top = rows[0]
    spine = {r: pos[(r, spine_col)] for r in rows}   # row -> ray color

    cells = {}  # (r,c) -> color, in canonical orientation

    # 1. downward chevrons from every ray cell
    for r in range(H):
        for c in range(W):
            src = r - abs(c - spine_col)
            if src in spine:
                cells[(r, c)] = spine[src]

    # 2. upward arms for the two ray cells farthest from the tip -> full X
    far_rows = {ray_top, ray_top + 1}
    for r in range(H):
        for c in range(W):
            src = r + abs(c - spine_col)
            if src in far_rows and src in spine and (r, c) not in cells:
                cells[(r, c)] = spine[src]

    # 3. each double marker floods its wedge through empty cells (ray cells block)
    doubles = [comp for comp in comps if comp is not main and len(comp) <= 2]
    for db in doubles:
        color = pos[db[0]]
        q = deque(db)
        seen = set()
        while q:
            r, c = q.popleft()
            if (r, c) in seen or not (0 <= r < H and 0 <= c < W):
                continue
            if (r, c) in cells:
                continue
            seen.add((r, c))
            cells[(r, c)] = color
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q.append((r + dr, c + dc))

    T_canon = [[cells.get((r, c)) for c in range(W)] for r in range(H)]
    return _rotk(T_canon, (4 - k) % 4)   # rotate mask back to original orientation


def apply_T(input_grid, T):
    """Copy the input, overwriting only the cells the mask marks."""
    out = [row[:] for row in input_grid]
    for r in range(len(out)):
        for c in range(len(out[0])):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
