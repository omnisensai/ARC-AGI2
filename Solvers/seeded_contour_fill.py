"""
Puzzle: 8f3a5a89
Rule name: seeded_contour_fill

Transformation rule:
Starting from the unique 6 marker, flood-fill through the background while
treating only edge-touching 1-clusters as barriers. Draw the exposed boundary
of that reachable region in 7. Preserve the 6 marker and any 1-clusters that
touch or lie inside the reachable region; remove all others.

The edge-barrier insight implicitly handles three wall cases:
  - 1-clusters touching the grid edge        -> block the flood (barriers)
                                                 and form the contour walls
                                                 the 7 halo wraps against
  - 1-clusters NOT touching the grid edge    -> reached by the flood,
                                                 preserved as walls but do
                                                 NOT cause halo around them
                                                 (interior obstacles)
  - 1-clusters not adjacent to the reachable
    region at all                            -> removed (become background)

Validation: training 3/3 + test pass on the official puzzle JSON.
"""

from collections import deque

SEED, WALL, PAINT, BG = 6, 1, 7, 8
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))


def _bfs(start, h, w, passable):
    """BFS from start, expanding to N4 neighbors satisfying passable(r, c)."""
    seen = {start}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in N4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and passable(nr, nc):
                seen.add((nr, nc))
                q.append((nr, nc))
    return seen


def solve(input_grid):
    h, w = len(input_grid), len(input_grid[0])

    seed = next(
        (r, c) for r in range(h) for c in range(w) if input_grid[r][c] == SEED
    )

    # Reachable background region from seed; walls block.
    reachable = _bfs(seed, h, w, lambda r, c: input_grid[r][c] != WALL)

    # Classify wall components: structural (halo), interior (preserved, no halo),
    # or unreachable (removed entirely).
    structural = set()
    interior = set()
    visited = set()
    for r in range(h):
        for c in range(w):
            if input_grid[r][c] != WALL or (r, c) in visited:
                continue
            comp = _bfs((r, c), h, w, lambda rr, cc: input_grid[rr][cc] == WALL)
            visited |= comp

            touches_region = any(
                (r2 + dr, c2 + dc) in reachable
                for r2, c2 in comp
                for dr, dc in N4
                if 0 <= r2 + dr < h and 0 <= c2 + dc < w
            )
            if not touches_region:
                continue  # unreachable wall -> removed

            touches_edge = any(
                r2 in (0, h - 1) or c2 in (0, w - 1) for r2, c2 in comp
            )
            if touches_edge:
                structural |= comp
            else:
                interior |= comp

    # Build output. Halo is painted on reachable cells that are on the grid edge
    # or adjacent to a structural wall.
    out = [[BG] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if input_grid[r][c] == SEED:
                out[r][c] = SEED
            elif (r, c) in structural or (r, c) in interior:
                out[r][c] = WALL
            elif (r, c) in reachable:
                on_edge = r in (0, h - 1) or c in (0, w - 1)
                touches_structural = any(
                    (r + dr, c + dc) in structural for dr, dc in N8
                )
                if on_edge or touches_structural:
                    out[r][c] = PAINT
    return out
