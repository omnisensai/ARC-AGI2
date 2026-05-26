"""Canonical latent-T solver for ARC puzzle b942fd60.

Rule (ray-bouncing / billiard):
  A single seed cell of color 2 sits on the left edge and emits a ray of 2s
  travelling rightward.  The ray advances over background cells (0).  When the
  next cell in its path is a colored marker (3/6/7/8), the ray stops in the cell
  immediately before the marker; that cell becomes a "turn point" which emits
  two fresh rays in the perpendicular directions.  Each emitted ray propagates
  the same way (advancing over background, reflecting at markers), so the trace
  grows as a tree of 2-coloured lines.  Markers, edges and already painted cells
  are never overwritten except that background cells along ray paths become 2.

infer_T builds the latent mask of cells that the bouncing trace covers;
apply_T copies the input and writes color 2 into exactly those masked cells.
"""

from collections import deque


def infer_T(input_grid):
    """Return latent mask: {(r, c): 2} for every background cell on the trace."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    def is_open(r, c):
        # cell exists and is not a (non-2) marker -> a ray may travel over it
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] in (0, 2)

    # locate the unique seed of color 2
    start = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                start = (r, c)
                break
        if start is not None:
            break

    mask = {}
    if start is None:
        return mask

    mask[start] = 2

    # BFS over directed rays; each ray is (row, col, dr, dc) launched from a point
    seen = set()
    rays = deque()
    rays.append((start[0], start[1], 0, 1))  # seed shoots to the right
    while rays:
        r, c, dr, dc = rays.popleft()
        if (r, c, dr, dc) in seen:
            continue
        seen.add((r, c, dr, dc))
        cr, cc = r, c
        while True:
            nr, nc = cr + dr, cc + dc
            if not (0 <= nr < H and 0 <= nc < W):
                break  # ran off the grid
            if input_grid[nr][nc] not in (0, 2):
                # blocked by a marker: (cr, cc) is a turn point -> emit perpendicular rays
                rays.append((cr, cc, dc, dr))
                rays.append((cr, cc, -dc, -dr))
                break
            cr, cc = nr, nc
            mask[(cr, cc)] = 2

    return mask


def apply_T(input_grid, T):
    """Copy the grid and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
