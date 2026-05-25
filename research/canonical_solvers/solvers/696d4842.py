"""Canonical latent-T solver for ARC puzzle 696d4842.

Rule (per snake/path object):
  The grid contains two multi-cell "snakes" (bent line paths, each a single
  color with two endpoints) and two single-cell markers of other colors.
  Each snake has exactly one endpoint whose outward arm direction points at a
  marker lying in line with it (same row or column, separated by empty cells).
  Transform:
    1. Extend that endpoint toward its marker, filling the N empty cells in
       between with the snake's own color (stopping just before the marker).
    2. Recolor the first N cells of the OTHER endpoint's arm (walking inward
       along the path) with the marker's color.
"""


def _find_components(grid):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                col = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[rr][cc] or grid[rr][cc] != col:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((rr + dr, cc + dc))
                comps.append((col, cells))
    return comps


def _endpoints(cells):
    cset = set(cells)
    eps = []
    for (r, c) in cells:
        nb = sum(
            1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (r + dr, c + dc) in cset
        )
        if nb <= 1:
            eps.append((r, c))
    return eps


def _arm_dir(ep, cells):
    """Outward direction from an endpoint (opposite of its single neighbor)."""
    cset = set(cells)
    r, c = ep
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if (r + dr, c + dc) in cset:
            return (-dr, -dc)
    return (0, 0)


def _path_order_from(ep, cells):
    """Walk the snake path starting at endpoint ep; return ordered cell list."""
    cset = set(cells)
    order = [ep]
    prev = None
    cur = ep
    while True:
        nxts = [
            (cur[0] + dr, cur[1] + dc)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (cur[0] + dr, cur[1] + dc) in cset
            and (cur[0] + dr, cur[1] + dc) != prev
        ]
        if not nxts:
            break
        prev = cur
        cur = nxts[0]
        order.append(cur)
    return order


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    comps = _find_components(input_grid)
    snakes = [(col, cells) for col, cells in comps if len(cells) > 1]

    T = {}
    for col, cells in snakes:
        eps = _endpoints(cells)
        if len(eps) != 2:
            continue

        # Find the endpoint whose outward arm points at an aligned marker.
        chosen = None
        for ep in eps:
            dr, dc = _arm_dir(ep, cells)
            if (dr, dc) == (0, 0):
                continue
            r, c = ep[0] + dr, ep[1] + dc
            steps = 0
            while 0 <= r < H and 0 <= c < W:
                v = input_grid[r][c]
                if v != 0:
                    if v != col:
                        chosen = (ep, (dr, dc), v, steps)
                    break
                r += dr
                c += dc
                steps += 1
            if chosen:
                break
        if not chosen:
            continue

        ep, (dr, dc), mcol, n = chosen

        # 1. Extend the endpoint toward the marker with the snake's color.
        r, c = ep[0] + dr, ep[1] + dc
        for _ in range(n):
            T[(r, c)] = col
            r += dr
            c += dc

        # 2. Recolor the first n cells of the other endpoint's arm.
        other = eps[1] if eps[0] == ep else eps[0]
        order = _path_order_from(other, cells)
        for k in range(min(n, len(order))):
            T[order[k]] = mcol

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
