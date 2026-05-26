def _bg(grid):
    from collections import Counter
    c = Counter(v for row in grid for v in row)
    return c.most_common(1)[0][0]


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and grid[ny][nx] == color:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps


def _min_period(seq):
    n = len(seq)
    for p in range(1, n + 1):
        if all(seq[i] == seq[i % p] for i in range(n)):
            return seq[:p]
    return seq


def infer_T(input_grid):
    """Each color-1 blob (head) carries a short colored 'tail' on exactly one
    side. The tail is a pattern that repeats along its axis pointing away from
    the blob. Build a mask that tiles that pattern from the blob to the grid
    edge, overwriting background cells along the way."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    T = {}
    blobs = _components(input_grid, 1)
    for cells in blobs:
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        # Find the side of the blob adjacent to non-bg, non-1 (tail) cells.
        candidates = []
        for d in ('up', 'down', 'left', 'right'):
            if d == 'up':
                probe = [(r0 - 1, c) for c in range(c0, c1 + 1)]
            elif d == 'down':
                probe = [(r1 + 1, c) for c in range(c0, c1 + 1)]
            elif d == 'left':
                probe = [(r, c0 - 1) for r in range(r0, r1 + 1)]
            else:
                probe = [(r, c1 + 1) for r in range(r0, r1 + 1)]
            colored = [(y, x) for (y, x) in probe
                       if 0 <= y < H and 0 <= x < W
                       and input_grid[y][x] != bg and input_grid[y][x] != 1]
            if colored:
                candidates.append((d, colored))
        if not candidates:
            continue
        d, colored = candidates[0]
        vertical = d in ('up', 'down')
        if vertical:
            cols = sorted(set(x for y, x in colored))
            step = -1 if d == 'up' else 1
            start_r = (r0 - 1) if d == 'up' else (r1 + 1)
            tail = []
            r = start_r
            while 0 <= r < H:
                vals = tuple(input_grid[r][c] for c in cols)
                if all(v == bg for v in vals):
                    break
                tail.append(vals)
                r += step
            if not tail:
                continue
            period = _min_period(tail)
            r, i = start_r, 0
            while 0 <= r < H:
                vals = period[i % len(period)]
                for ci, c in enumerate(cols):
                    if vals[ci] != bg:
                        T[(r, c)] = vals[ci]
                r += step
                i += 1
        else:
            rows = sorted(set(y for y, x in colored))
            step = -1 if d == 'left' else 1
            start_c = (c0 - 1) if d == 'left' else (c1 + 1)
            tail = []
            c = start_c
            while 0 <= c < W:
                vals = tuple(input_grid[r][c] for r in rows)
                if all(v == bg for v in vals):
                    break
                tail.append(vals)
                c += step
            if not tail:
                continue
            period = _min_period(tail)
            c, i = start_c, 0
            while 0 <= c < W:
                vals = period[i % len(period)]
                for ri, r in enumerate(rows):
                    if vals[ri] != bg:
                        T[(r, c)] = vals[ri]
                c += step
                i += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
