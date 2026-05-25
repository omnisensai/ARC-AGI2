from collections import deque


def infer_T(input_grid):
    # Color 1 behaves like liquid (water). Cells that are neither 0 nor 1 are
    # solid walls; 0 cells are empty space. Simulate the water settling under
    # gravity: each water unit falls straight down whenever the cell below is
    # empty, and only spreads sideways when blocked from below, coming to rest
    # in the lowest cell it can reach. Total amount of water is conserved.
    #
    # T is a change mask the size of the grid: T[r][c] holds the value to write
    # (1 for newly settled water, 0 for water that drained away) or None to
    # leave the input cell untouched.
    H, W = len(input_grid), len(input_grid[0])
    g = [row[:] for row in input_grid]

    def isempty(r, c):
        return 0 <= r < H and 0 <= c < W and g[r][c] == 0

    while True:
        moved = False
        for r in range(H - 1, -1, -1):
            for c in range(W):
                if g[r][c] != 1:
                    continue
                # Find the lowest empty cell reachable by the flow rule: water
                # falls straight down when it can, otherwise spreads sideways.
                seen = {(r, c)}
                q = deque([(r, c)])
                best = None
                while q:
                    rr, cc = q.popleft()
                    if isempty(rr + 1, cc):
                        nxt = (rr + 1, cc)
                        if nxt not in seen:
                            seen.add(nxt)
                            q.append(nxt)
                            if best is None or nxt[0] > best[0]:
                                best = nxt
                        continue
                    for dc in (-1, 1):
                        nxt = (rr, cc + dc)
                        if isempty(*nxt) and nxt not in seen:
                            seen.add(nxt)
                            q.append(nxt)
                            if best is None or nxt[0] > best[0]:
                                best = nxt
                if best is not None and best[0] > r:
                    g[best[0]][best[1]] = 1
                    g[r][c] = 0
                    moved = True
        if not moved:
            break

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            now = 1 if g[r][c] == 1 else (input_grid[r][c] if input_grid[r][c] != 1 else 0)
            if now != input_grid[r][c]:
                T[r][c] = now
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
