from collections import deque


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and grid[ny][nx] == color and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            q.append((ny, nx))
                out.append(cells)
    return out


def infer_T(input_grid):
    """Each color-2 'bracket' is a 3-sided box. Its open side faces the interior;
    the opposite full side is a reflection axis. The color-5 shape sitting on the
    OUTER side of that axis is reflected across the axis into the interior, and its
    original cells are cleared."""
    H, W = len(input_grid), len(input_grid[0])
    brackets = _components(input_grid, 2)
    shapes = _components(input_grid, 5)

    # describe each bracket: axis line + orientation + which side is "outer"
    axes = []  # (orient, axis_value)  orient 'col' or 'row'
    for cc in brackets:
        cset = set(cc)
        rs = [y for y, x in cc]
        cs = [x for y, x in cc]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        top = all((r0, c) in cset for c in range(c0, c1 + 1))
        bot = all((r1, c) in cset for c in range(c0, c1 + 1))
        left = all((r, c0) in cset for r in range(r0, r1 + 1))
        right = all((r, c1) in cset for r in range(r0, r1 + 1))
        # opening = the side that is NOT full; axis = opposite side
        if not right:
            axes.append(('col', c0))
        elif not left:
            axes.append(('col', c1))
        elif not bot:
            axes.append(('row', r0))
        elif not top:
            axes.append(('row', r1))

    clears = set()
    draws = {}  # (r,c) -> 5
    for cc in shapes:
        for (y, x) in cc:
            clears.add((y, x))
        rs = [y for y, x in cc]
        cs = [x for y, x in cc]
        cy = sum(rs) / len(rs)
        cx = sum(cs) / len(cs)
        # find the axis this shape belongs to: the shape lies outside that axis,
        # and reflection lands inside grid. Choose nearest axis of matching orient
        best = None
        bestd = None
        for orient, val in axes:
            coord = cy if orient == 'row' else cx
            d = abs(coord - val)
            if bestd is None or d < bestd:
                bestd = d
                best = (orient, val)
        orient, val = best
        for (y, x) in cc:
            if orient == 'col':
                ny, nx = y, 2 * val - x
            else:
                ny, nx = 2 * val - y, x
            draws[(ny, nx)] = 5

    T = {}
    for cell in clears:
        T[cell] = 0
    for cell, v in draws.items():
        T[cell] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(out), len(out[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
