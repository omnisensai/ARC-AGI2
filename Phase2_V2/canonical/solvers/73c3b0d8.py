def find_wall(grid):
    """Locate the solid line of 2s. Returns ('h', row) for a horizontal wall."""
    H, W = len(grid), len(grid[0])
    for r in range(H):
        if all(v == 2 for v in grid[r]):
            return ('h', r)
    for c in range(W):
        if all(grid[r][c] == 2 for r in range(H)):
            return ('v', c)
    return None


def infer_T(input_grid):
    """Latent transformation mask {(r,c): color}.

    Structure: a horizontal wall of 2s plus single-cell 4 "balls". Gravity pulls
    every ball one step downward. A ball that, after moving, lands directly above
    the wall has "hit" it; it bounces, emitting an upward-opening 45-degree cone
    (V) whose apex is the impact cell and whose arms extend to the grid edges.
    Balls that do not reach the wall (including those below it) simply shift down
    one cell. The mask records every cell that should hold a 4 in the output.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    wall = find_wall(input_grid)
    balls = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]

    if wall is None or wall[0] != 'h':
        # No usable horizontal wall: just drop every ball one row.
        for (r, c) in balls:
            nr = r + 1 if r + 1 < H else r
            T[(nr, c)] = 4
        return T

    wr = wall[1]
    for (r, c) in balls:
        nr = r + 1  # move down one step under gravity
        if nr >= H:
            nr = r
        if nr == wr:
            # Cannot enter the wall; the ball is resting against it -> impact.
            nr = wr - 1
        hit = (nr == wr - 1 and r < wr)  # landed directly above the wall
        if hit:
            # Bounce: upward-opening cone with apex at the impact cell.
            T[(nr, c)] = 4
            k = 1
            while True:
                rr = nr - k
                if rr < 0:
                    break
                for cc in (c - k, c + k):
                    if 0 <= cc < W:
                        T[(rr, cc)] = 4
                k += 1
        else:
            T[(nr, c)] = 4
    return T


def apply_T(input_grid, T):
    """Copy the input, clear the moving balls, then stamp the mask."""
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if out[r][c] == 4:
                out[r][c] = 0
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
