def _components(grid, bg=0):
    H, W = len(grid), len(grid[0])
    seen = [[False]*W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                y, x = stack.pop()
                if not (0 <= y < H and 0 <= x < W) or seen[y][x]:
                    continue
                if grid[y][x] != color:
                    continue
                seen[y][x] = True
                cells.append((y, x))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    stack.append((y+dy, x+dx))
            comps.append((color, cells))
    return comps


# Direction each marker color slides toward (the latent rule of this task):
# the hollow square translates until it hits the grid edge in this direction.
_DIR = {6: (-1, 0), 4: (1, 0), 3: (0, -1), 8: (0, 1)}


def infer_T(input_grid):
    """Infer a latent mask: cells to clear (the object's old footprint) and
    cells to paint (the object translated to the edge in its color's direction)."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for color, cells in _components(input_grid):
        if color not in _DIR:
            continue
        dy, dx = _DIR[color]
        rs = [y for y, x in cells]
        cs = [x for y, x in cells]
        top, bot, left, right = min(rs), max(rs), min(cs), max(cs)
        # how far it can slide before any cell leaves the grid
        if dy < 0:
            steps = top
        elif dy > 0:
            steps = (H - 1) - bot
        elif dx < 0:
            steps = left
        else:
            steps = (W - 1) - right
        sy, sx = dy * steps, dx * steps
        # clear old footprint
        for y, x in cells:
            T[(y, x)] = 0
        # paint at new location (overrides clears where they overlap)
        for y, x in cells:
            T[(y + sy, x + sx)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
