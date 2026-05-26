from collections import Counter


def _analyze(input_grid):
    """Identify background, the full-grid crossing line color, the hollow box
    color, and the box bounding rectangle."""
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]
    # The line color spans the whole grid, so it shows up on the grid border.
    edge = set()
    for c in range(W):
        edge.add(input_grid[0][c])
        edge.add(input_grid[H - 1][c])
    for r in range(H):
        edge.add(input_grid[r][0])
        edge.add(input_grid[r][W - 1])
    edge.discard(bg)
    line = next(iter(edge))
    box = next(c for c in cnt if c not in (bg, line))
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == box]
    rmin = min(r for r, _ in cells)
    rmax = max(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    cmax = max(c for _, c in cells)
    return bg, line, box, rmin, rmax, cmin, cmax


def infer_T(input_grid):
    """Build a latent mask {(r, c): new_color}. The vertical line snaps to the
    box's right edge (cmax) and the horizontal line snaps to the box's top edge
    (rmin), both drawn only outside the box span; the box interior and the old
    line cells are cleared to background. The box border itself is left intact.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg, line, box, rmin, rmax, cmin, cmax = _analyze(input_grid)
    T = {}
    # Erase every existing line-color cell back to background.
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == line:
                T[(r, c)] = bg
    # Horizontal line -> row rmin, only outside the box's column span.
    for c in range(W):
        if not (cmin <= c <= cmax):
            T[(rmin, c)] = line
    # Vertical line -> col cmax, only outside the box's row span.
    for r in range(H):
        if not (rmin <= r <= rmax):
            T[(r, cmax)] = line
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
