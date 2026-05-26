def _markers(grid):
    """Locate the three colored marker cells (2, 3, 4)."""
    H, W = len(grid), len(grid[0])
    pts = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 0:
                pts[v] = (r, c)
    return pts


def _segment(p, q):
    """Inclusive straight (axis-aligned) segment between two collinear points."""
    (r1, c1), (r2, c2) = p, q
    cells = set()
    if r1 == r2:
        for c in range(min(c1, c2), max(c1, c2) + 1):
            cells.add((r1, c))
    else:  # c1 == c2
        for r in range(min(r1, r2), max(r1, r2) + 1):
            cells.add((r, c1))
    return cells


def _lpath(a, b, corner):
    """L-shaped path from a to b bending at corner."""
    return _segment(a, corner) | _segment(corner, b)


def infer_T(input_grid):
    """
    Latent mask: cells to paint color 5.

    Marker 4 is the hub. Two right-angle (L-shaped) paths emanate from it:
      - 4 -> 3 turning first horizontally (corner at 4's row, 3's column)
      - 4 -> 2 turning first vertically   (corner at 2's row, 4's column)
    The mask is all path cells except the three marker cells themselves.
    """
    H, W = len(input_grid), len(input_grid[0])
    pts = _markers(input_grid)
    T = [[None] * W for _ in range(H)]
    if not all(k in pts for k in (2, 3, 4)):
        return T

    hub = pts[4]
    t3 = pts[3]
    t2 = pts[2]

    path_3 = _lpath(hub, t3, (hub[0], t3[1]))   # horizontal-first
    path_2 = _lpath(hub, t2, (t2[0], hub[1]))   # vertical-first

    paint = (path_3 | path_2) - {hub, t3, t2}
    for (r, c) in paint:
        if 0 <= r < H and 0 <= c < W:
            T[r][c] = 5
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
