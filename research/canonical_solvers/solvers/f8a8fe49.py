"""Canonical solver for ARC puzzle f8a8fe49.

Structure: a rectangular "box" frame of color 2 with two complete parallel
walls (either the left/right vertical walls or the top/bottom horizontal
walls) and partial bracket-corners on the other axis. Color-5 marks sit
inside the box, clustered near each complete wall.

Rule: every 5 cell is removed from the interior and reflected across the
nearest complete wall to land outside the box; the coordinate along the wall
axis is preserved.
"""


def _find_box(g):
    H, W = len(g), len(g[0])
    twos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 2]
    if not twos:
        return None
    rs = [r for r, _ in twos]
    cs = [c for _, c in twos]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    left = sum(1 for r, c in twos if c == c0)
    top = sum(1 for r, c in twos if r == r0)
    # A wall is "complete" when its straight line of 2s spans the whole box side.
    vertical = (left == bh)   # full vertical (left/right) walls -> reflect on columns
    if not vertical:
        # sanity: ensure horizontal walls are the complete ones
        vertical = (left == bh and not (top == bw))
    return r0, r1, c0, c1, (left == bh)


def infer_T(input_grid):
    """Latent transformation mask: {(r, c): new_color}.

    Cells set to 0 clear the interior 5s; cells set to 5 are the reflected
    marks placed outside the box. Computed purely from input structure.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    box = _find_box(input_grid)
    if box is None:
        return T
    r0, r1, c0, c1, vertical = box

    fives = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    # Clear every interior 5.
    for r, c in fives:
        T[(r, c)] = 0
    # Reflect each 5 across the nearest complete wall.
    for r, c in fives:
        if vertical:
            nc = 2 * c0 - c if abs(c - c0) <= abs(c - c1) else 2 * c1 - c
            nr = r
        else:
            nr = 2 * r0 - r if abs(r - r0) <= abs(r - r1) else 2 * r1 - r
            nc = c
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
