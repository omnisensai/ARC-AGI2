"""Canonical latent-T solver for ARC puzzle cc9053aa.

Structure of every pair:
  - A maze of wall cells (color 8) sits on a background (color 0).
  - Two marker cells (color 9) lie in the exterior, each touching exactly one
    wall cell (the "entry" into the wall network).
  - One or more target markers (color 7) lie inside interior rooms.

Transformation: trace a path through the wall network connecting the two
entries.  The path may only use wall cells that (a) are NOT adjacent to a 7
marker (those wall segments are "blocked") and (b) lie on the boundary of free
space (touch at least one non-wall corridor cell, so the path hugs corridors
instead of cutting through solid wall).  Every wall cell on that path is
recolored to 9.

Canonical form:
    T = infer_T(input_grid)   # dict {(r,c): 9} latent mask of cells to change
    return apply_T(input_grid, T)
"""

from collections import deque


def _entry_wall(grid, marker, H, W):
    """The unique wall (8) cell 4-adjacent to a 9 marker."""
    r, c = marker
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == 8:
            return (nr, nc)
    return None


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    nines = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 9]
    sevens = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 7]

    T = {}
    if len(nines) < 2:
        return T

    # Wall cells that are "blocked": 4-adjacent to a 7 marker.
    blocked = set()
    for (r, c) in sevens:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == 8:
                blocked.add((nr, nc))

    def touches_corridor(r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] != 8:
                return True
        return False

    def allowed(r, c):
        return (input_grid[r][c] == 8
                and (r, c) not in blocked
                and touches_corridor(r, c))

    e0 = _entry_wall(input_grid, nines[0], H, W)
    e1 = _entry_wall(input_grid, nines[1], H, W)
    if e0 is None or e1 is None:
        return T

    # Shortest path through allowed wall cells from one entry to the other.
    prev = {e0: None}
    q = deque([e0])
    while q:
        cur = q.popleft()
        if cur == e1:
            break
        r, c = cur
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < H and 0 <= nc < W and allowed(nr, nc)
                    and (nr, nc) not in prev):
                prev[(nr, nc)] = cur
                q.append((nr, nc))

    if e1 in prev:
        cur = e1
        while cur is not None:
            T[cur] = 9
            cur = prev[cur]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
