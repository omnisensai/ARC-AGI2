"""L0 grid coordinate library — substrate of coordinate algebra over (r,c).

Authoritative implementations of the atoms in CONTRACTS_L0.md. L0 family
canonical solvers INLINE the relevant functions (so SFT records and the
gate's subprocess runner are self-contained); this file is the source of
truth the inlines are drawn from.

Naming/convention:
  - bg() returns the most-common colour. A family's contract must DECLARE that
    bg = most-common; do not assume it elsewhere.
  - Connectivity (4 or 8) must be PASSED explicitly. No default.
  - Coordinate sets are returned as set[tuple[int,int]].
"""
from collections import Counter, deque


# ---------- 1. cell / colour / background --------------------------------
def bg(g):
    """Most common colour in g. (Family contract must declare bg = most-common.)"""
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def cells_of_color(g, color):
    H, W = len(g), len(g[0])
    return {(r, c) for r in range(H) for c in range(W) if g[r][c] == color}


def nonbg_cells(g):
    bv = bg(g)
    H, W = len(g), len(g[0])
    return {(r, c) for r in range(H) for c in range(W) if g[r][c] != bv}


# ---------- 2. neighborhoods ---------------------------------------------
def neighbors4(r, c):
    return [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]


def neighbors8(r, c):
    return [(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]


# ---------- 3. positional atoms ------------------------------------------
def corner_cells(H, W):
    return [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]


def edge_cells(H, W, side):
    if side == "top":    return [(0, c) for c in range(W)]
    if side == "bottom": return [(H - 1, c) for c in range(W)]
    if side == "left":   return [(r, 0) for r in range(H)]
    if side == "right":  return [(r, W - 1) for r in range(H)]
    raise ValueError(side)


# ---------- 4. bbox / anchor ---------------------------------------------
def bbox(cells):
    """(top, left, bottom, right) of a non-empty cell set."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def anchor(cells, kind="bbox_top_left"):
    if kind == "bbox_top_left":
        t, l, _, _ = bbox(cells); return (t, l)
    raise ValueError(kind)


# ---------- 5. components (connectivity MUST be passed) ------------------
def find_components(g, conn):
    """Connected components of same-colour non-bg cells under declared connectivity.

    Returns a list of cell sets, in canonical order (sorted by (min_row, min_col)
    of each component) so labelling is deterministic across runs.
    """
    assert conn in (4, 8), "connectivity must be 4 or 8 (no default)"
    H, W = len(g), len(g[0])
    bv = bg(g)
    nb = neighbors4 if conn == 4 else neighbors8
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv and not seen[r][c]:
                color = g[r][c]
                comp = set()
                q = deque([(r, c)])
                seen[r][c] = True
                while q:
                    y, x = q.popleft()
                    comp.add((y, x))
                    for (ny, nx) in nb(y, x):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == color:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(comp)
    out.sort(key=lambda s: (min(r for r, _ in s), min(c for _, c in s)))
    return out


# ---------- 6. boundary / interior ---------------------------------------
def boundary_of(cells, conn=4):
    """Cells in `cells` with at least one (4- or 8-)neighbour OUTSIDE `cells`.
    Out-of-grid neighbours count as outside, so edge cells are boundary.
    """
    assert conn in (4, 8)
    nb = neighbors4 if conn == 4 else neighbors8
    s = set(cells)
    return {(r, c) for (r, c) in s if any(p not in s for p in nb(r, c))}


def interior_of(cells, conn=4):
    """object_interior: cells of `cells` that are NOT on its boundary."""
    return set(cells) - boundary_of(cells, conn)
