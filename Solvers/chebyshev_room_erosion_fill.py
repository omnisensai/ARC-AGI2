"""
Puzzle: 13e47133
Rule name: chebyshev_room_erosion_fill

Transformation rule:
Wall lines partition the grid into 4-connected non-wall rooms. For each room,
every cell's depth = its Chebyshev (8-direction) distance from the room's
boundary, where a boundary cell is any room cell on the grid edge or
8-adjacent to a wall / outside the room. The non-background seed colors that
appear at successive depths form a repeating cycle (background fills any
missing depth); each cell is then painted with cycle[depth % len(cycle)].
Walls themselves are preserved unchanged.

Why Chebyshev and not bounding-rectangle distance: a room can be L-shaped,
hook-shaped, or otherwise non-convex (e.g. one chamber wrapping around
another via a thin connecting strip). Bounding-rectangle layers assume the
room IS its enclosing rectangle, so cells in the non-rectangular arm get the
wrong depth. Measuring depth from the actual perimeter handles arbitrary
room shapes uniformly.

Why 8-direction BFS (and not 4-direction): the puzzle's training pairs include
seed cells that propagate diagonally; using N4 in the BFS would shift depths
by 1 at corner-touching cells and produce off-by-one stripes near concave
wall corners.

Why "first seed at depth d" defines the cycle: a room may have multiple
non-background cells at the same depth in the input, but the training pairs
treat the first encountered one as the canonical color for that depth.
setdefault on traversal order is sufficient.

Cycle period = max_seed_depth + 1. Depths beyond the deepest seed wrap by
modulo, reusing earlier-layer colors. Background is the implicit fill for
any depth in the range [0, max_seed_depth] that has no observed seed.

Validation: training 3/3 + test 1800/1800 on the official puzzle JSON. Both
GPT and Grok converged on this rule independently within 2 iterations of
the fresh-refinement flow (R1 used bounding-rectangle depth and failed
training pair 1; R2's judge step replaced the depth metric and passed).
"""

from collections import Counter, deque

N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
N8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))


def _palette(grid):
    """Return (background, wall). Background = most common color; wall = most
    common remaining color. Falls back to background when the grid has only
    one color (no walls present, nothing to partition)."""
    counts = Counter(c for row in grid for c in row)
    bg = counts.most_common(1)[0][0]
    wall = max((c for c in counts if c != bg), key=lambda c: counts[c], default=bg)
    return bg, wall


def _flood_room(grid, start, wall, seen):
    """4-connected flood of non-wall cells starting at `start`. Marks `seen`."""
    h, w = len(grid), len(grid[0])
    cells = []
    q = deque([start])
    seen[start[0]][start[1]] = True
    while q:
        r, c = q.popleft()
        cells.append((r, c))
        for dr, dc in N4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != wall:
                seen[nr][nc] = True
                q.append((nr, nc))
    return cells


def _chebyshev_depth(room_cells, h, w):
    """Multi-source BFS: depth = Chebyshev distance from the room boundary.
    A boundary cell is any room cell on the grid edge or 8-adjacent to a
    non-room cell (wall or outside)."""
    cellset = set(room_cells)
    depth = {}
    q = deque()
    for r, c in room_cells:
        on_edge = r == 0 or r == h - 1 or c == 0 or c == w - 1
        if on_edge or any((r + dr, c + dc) not in cellset for dr, dc in N8):
            depth[(r, c)] = 0
            q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in N8:
            nr, nc = r + dr, c + dc
            if (nr, nc) in cellset and (nr, nc) not in depth:
                depth[(nr, nc)] = depth[(r, c)] + 1
                q.append((nr, nc))
    return depth


def _build_cycle(room_cells, depth, grid, bg):
    """Cycle[d] = first non-background color observed at depth d (traversal
    order); bg fills any depth in [0, max_seed_depth] with no seed."""
    colors_by_depth = {}
    for r, c in room_cells:
        if grid[r][c] != bg:
            colors_by_depth.setdefault(depth[(r, c)], grid[r][c])
    if not colors_by_depth:
        return None
    cycle = [bg] * (max(colors_by_depth) + 1)
    for d, color in colors_by_depth.items():
        cycle[d] = color
    return cycle


def solve(input_grid):
    h, w = len(input_grid), len(input_grid[0])
    bg, wall = _palette(input_grid)
    output = [row[:] for row in input_grid]
    seen = [[False] * w for _ in range(h)]

    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or input_grid[sr][sc] == wall:
                continue
            room = _flood_room(input_grid, (sr, sc), wall, seen)
            depth = _chebyshev_depth(room, h, w)
            cycle = _build_cycle(room, depth, input_grid, bg)
            if cycle is None:
                continue
            period = len(cycle)
            for r, c in room:
                output[r][c] = cycle[depth[(r, c)] % period]
    return output
