def _components(grid, fg):
    """4-connected components of foreground color `fg`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == fg and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != fg:
                        continue
                    seen.add((x, y))
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((x + dx, y + dy))
                comps.append(cells)
    return comps


def _classify(cells):
    """Assign a color to a shape from its geometry (size + fill + line-ness)."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    n = len(cells)
    full = (n == h * w)          # bounding box completely filled
    is_line = (h == 1 or w == 1)  # straight 1-wide line

    if n == 2:
        return 9                 # domino / line of two
    if n == 3:
        # line of three -> 2 ; bent L-tromino -> 4
        return 2 if (full and is_line) else 4
    if n == 4:
        return 8                 # S/Z tetromino
    if n == 5:
        return 3                 # plus / cross
    if n == 6:
        return 5                 # filled 2x3 rectangle
    return None


def infer_T(input_grid):
    """Latent mask: {(r,c): new_color} computed from input structure alone.

    Foreground = the non-background color forming the shapes. Background is the
    most frequent color. Each 4-connected foreground component is recolored
    according to its geometric class.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    # foreground is the (single) other color present
    fgs = [v for v in counts if v != bg]
    T = {}
    for fg in fgs:
        for cells in _components(input_grid, fg):
            col = _classify(cells)
            if col is None:
                continue
            for (r, c) in cells:
                T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
