from collections import deque


def infer_T(input_grid):
    """Latent mask: the shortest 4-connected path of background (0) cells
    connecting the two '2' markers gets recolored to 4. Walls are color 1.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background is the most common color (0 in this task).
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The two endpoint markers (color 2).
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]

    T = [[None] * W for _ in range(H)]
    if len(markers) < 2:
        return T

    start, goal = markers[0], markers[1]

    # BFS through background cells (markers are traversable as endpoints),
    # avoiding any non-background, non-marker cell (e.g. the 1 walls).
    def passable(r, c):
        return input_grid[r][c] == bg or input_grid[r][c] == 2

    prev = {start: None}
    q = deque([start])
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            break
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in prev and passable(nr, nc):
                prev[(nr, nc)] = (r, c)
                q.append((nr, nc))

    if goal not in prev:
        return T

    # Reconstruct path; mark only the background cells along it.
    cur = goal
    while cur is not None:
        r, c = cur
        if input_grid[r][c] == bg:
            T[r][c] = 4
        cur = prev[cur]

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
