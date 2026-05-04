"""
Puzzle: 8f3a5a89
Rule name: seeded_reachable_floodfill_trace

Transformation rule:
Flood-fill from the unique seed (6) through background, treating walls (1)
as blockers. Each wall component falls into one of three cases:
  - Does NOT touch the reachable region        -> removed (becomes background)
  - Touches reachable region AND a grid edge   -> structural; gets a halo
  - Touches reachable region but NO grid edge  -> preserved without halo
                                                  (interior obstacle)
Paint the halo (7) on every reachable cell that is either on the grid edge
or adjacent (8-neighborhood) to a structural wall. Everything else in the
output is background (8). The seed itself is preserved.

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
