"""Canonical solver for ARC puzzle 28e73c20.

Rule: the input is a blank (all-zero) square grid. The output draws a single
square spiral wall of color 3 starting at the top-left corner (0,0), moving
right along the top, turning clockwise, and curling inward with a 1-cell gap
between consecutive arms. The transformation mask T marks exactly the cells the
spiral pen traverses.

infer_T simulates the pen: it advances straight when the next cell is free and
keeps a clean 1-cell gap from every already-drawn arm (no drawn orthogonal
neighbor except the trailing cell); otherwise it turns clockwise. When it can
no longer make such a step it performs one final closing step in the
turn-left/clockwise direction iff that cell AND the cell beyond it are still
free (this completes the innermost curl for even-sized grids, while leaving the
exact-center pocket untouched for odd-sized grids).
"""


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    FILL = 3
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up (clockwise)
    mark = [[False] * W for _ in range(H)]

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    def marked(r, c):
        return inb(r, c) and mark[r][c]

    def free(r, c):
        return inb(r, c) and not mark[r][c]

    def can_step(r, c, pr, pc):
        # Cell must be free and keep a 1-cell gap: no drawn orthogonal neighbor
        # except the cell we just came from.
        if not free(r, c):
            return False
        for dr, dc in dirs:
            ar, ac = r + dr, c + dc
            if (ar, ac) == (pr, pc):
                continue
            if marked(ar, ac):
                return False
        return True

    di = 0
    r = c = 0
    mark[r][c] = True
    while True:
        for ndi in (di, (di + 1) % 4):  # prefer straight, else turn clockwise
            dr, dc = dirs[ndi]
            nr, nc = r + dr, c + dc
            if can_step(nr, nc, r, c):
                di = ndi
                r, c = nr, nc
                mark[r][c] = True
                break
        else:
            break

    # Final closing step: extend the curl by one cell in the clockwise-turn
    # direction iff that cell and the cell beyond it are both still free.
    tdr, tdc = dirs[(di + 1) % 4]
    nr, nc = r + tdr, c + tdc
    br, bc = r + 2 * tdr, c + 2 * tdc
    if free(nr, nc) and free(br, bc):
        mark[nr][nc] = True

    T = [[FILL if mark[r][c] else None for c in range(W)] for r in range(H)]
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
