from collections import deque


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(g):
    """8-connected non-zero components."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0 and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != 0 and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def infer_T(input_grid):
    """Each object is a solid rectangle of 9s with a zigzag fault line of 6s
    that fully crosses the object's SHORTER dimension. The object is torn
    apart along the longer dimension: cells on one side of the fault shift one
    step away from it, cells on the other side shift one step the other way,
    and the 6 (fault) cells are removed. The latent mask T records every
    original cell to clear plus every (target cell -> color) to place.
    """
    H, W = len(input_grid), len(input_grid[0])
    clear = set()   # original object cells -> background
    place = {}      # (r, c) -> color
    for cells in _components(input_grid):
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        for (r, c) in cells:
            clear.add((r, c))
        vertical = bh >= bw  # taller/square -> split top/bottom, per column
        if vertical:
            for c in range(c0, c1 + 1):
                six_r = None
                for r in range(r0, r1 + 1):
                    if input_grid[r][c] == 6:
                        six_r = r
                        break
                for r in range(r0, r1 + 1):
                    v = input_grid[r][c]
                    if v == 0 or v == 6:
                        continue
                    if six_r is None:
                        place[(r, c)] = v
                    elif r < six_r:
                        place[(r - 1, c)] = v
                    else:
                        place[(r + 1, c)] = v
        else:
            for r in range(r0, r1 + 1):
                six_c = None
                for c in range(c0, c1 + 1):
                    if input_grid[r][c] == 6:
                        six_c = c
                        break
                for c in range(c0, c1 + 1):
                    v = input_grid[r][c]
                    if v == 0 or v == 6:
                        continue
                    if six_c is None:
                        place[(r, c)] = v
                    elif c < six_c:
                        place[(r, c - 1)] = v
                    else:
                        place[(r, c + 1)] = v
    return (clear, place, H, W)


def apply_T(input_grid, T):
    clear, place, H, W = T
    out = [row[:] for row in input_grid]
    for (r, c) in clear:
        out[r][c] = 0
    for (r, c), v in place.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out
