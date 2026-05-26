def _components(grid, color):
    """Return 8-connected components (lists of cells) of `color`."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in seen or not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if grid[cr][cc] != color:
                        continue
                    seen.add((cr, cc))
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((cr + dr, cc + dc))
                comps.append(comp)
    return comps


def _encloses_hole(comp, H, W):
    """True if `comp` (a set of cells) fully encloses a background region
    that is not 4-connected to the grid border."""
    cs = set(comp)
    reach = set()
    stack = []
    for r in range(H):
        for c in range(W):
            if (r == 0 or r == H - 1 or c == 0 or c == W - 1) and (r, c) not in cs:
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        if (r, c) in reach or not (0 <= r < H and 0 <= c < W) or (r, c) in cs:
            continue
        reach.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    for r in range(H):
        for c in range(W):
            if (r, c) not in cs and (r, c) not in reach:
                return True
    return False


def infer_T(input_grid):
    """Latent mask: every cell of a closed-loop (hole-enclosing) component of 1s
    is marked to become 8; all other cells stay as-is (None)."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for comp in _components(input_grid, 1):
        if _encloses_hole(comp, H, W):
            for r, c in comp:
                T[r][c] = 8
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
