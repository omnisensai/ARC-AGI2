"""Canonical solver for ARC puzzle d282b262.

Rule: every connected object (8-connectivity, non-background) keeps its row
span and slides rightward under "gravity" until it hits the right wall or an
already-settled object. Background is 0. Objects nearest the wall settle first,
then others stack against them.

Canonical form:
  - infer_T computes a latent mask T = {(r, c): new_color} describing the full
    set of non-background cells in their final (right-shifted) positions.
  - apply_T copies the input, clears all original object cells, and writes the
    masked cells.
"""


def _objects(grid):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    objs = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[cr][cc] or grid[cr][cc] == 0:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc, grid[cr][cc]))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((cr + dr, cc + dc))
                objs.append(cells)
    return objs


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    objs = _objects(input_grid)

    # Settle objects nearest the right wall first.
    info = sorted(objs, key=lambda cells: -max(c for _, c, _ in cells))

    occupied = set()
    T = {}
    for cells in info:
        shift = 0
        while True:
            trial = shift + 1
            ok = True
            for r, c, _ in cells:
                nc = c + trial
                if nc >= W or (r, nc) in occupied:
                    ok = False
                    break
            if ok:
                shift = trial
            else:
                break
        for r, c, v in cells:
            occupied.add((r, c + shift))
            T[(r, c + shift)] = v
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [[0 if input_grid[r][c] != 0 else input_grid[r][c]
            for c in range(W)] for r in range(H)]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
