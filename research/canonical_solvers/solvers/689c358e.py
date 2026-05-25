def _objects(g):
    """Connected components of non-background (not 6 border, not 7 fill) cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if g[r][c] not in (6, 7) and not seen[r][c]:
                color = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[rr][cc] or g[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                objs.append((color, cells))
    return objs


_DIRV = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
_OPP = {'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L'}


def infer_T(input_grid):
    """Build a latent mask {(r,c): new_color} of border cells to overwrite.

    Each interior object is a 'plus' shape whose arms have length 1 except for
    one longer arm (the tail). The arrow points OPPOSITE to the tail. Casting a
    ray from the plus center toward the pointing direction marks the hit border
    cell with the object's color; the border cell in the tail direction is 0.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for color, cells in _objects(input_grid):
        cellset = set(cells)

        def deg(cell):
            r, c = cell
            return sum(
                (r + dr, c + dc) in cellset
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )

        center = max(cells, key=deg)
        cr, cc = center
        arms = {'U': 0, 'D': 0, 'L': 0, 'R': 0}
        for (r, c) in cells:
            if (r, c) == center:
                continue
            if r < cr and c == cc:
                arms['U'] += 1
            elif r > cr and c == cc:
                arms['D'] += 1
            elif c < cc and r == cr:
                arms['L'] += 1
            elif c > cc and r == cr:
                arms['R'] += 1
        tail = max(arms, key=arms.get)
        point = _OPP[tail]

        # Ray from center toward the pointing direction until it leaves the
        # interior (hits the border of 6s): mark that border cell with color.
        dr, dc = _DIRV[point]
        r, c = cr, cc
        while 0 <= r < H and 0 <= c < W and input_grid[r][c] != 6:
            r += dr
            c += dc
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = color

        # Border cell in the tail direction gets a 0.
        dr2, dc2 = _DIRV[tail]
        r2, c2 = cr, cc
        while 0 <= r2 < H and 0 <= c2 < W and input_grid[r2][c2] != 6:
            r2 += dr2
            c2 += dc2
        if 0 <= r2 < H and 0 <= c2 < W:
            T[(r2, c2)] = 0

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
