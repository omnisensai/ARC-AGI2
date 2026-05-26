def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # Locate the template: the unique 3x3 block containing the marker color 4.
    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    T = {}
    if not fours:
        return T
    tr = min(r for r, c in fours)
    tc = min(c for r, c in fours)
    th = max(r for r, c in fours) - tr + 1
    tw = max(c for r, c in fours) - tc + 1
    template = [[input_grid[tr + i][tc + j] for j in range(tw)] for i in range(th)]

    # Split the template into its key cells (the 1/8 pattern) and the mark cells
    # (the positions holding the marker color 4).
    key = []        # (di, dj, color) for non-4 cells
    marks = []      # (di, dj) positions that hold 4
    for i in range(th):
        for j in range(tw):
            v = template[i][j]
            if v == 4:
                marks.append((i, j))
            else:
                key.append((i, j, v))

    # Scan every placement of the template across the grid. A target matches when
    # it reproduces the key pattern exactly and is empty (0) in every mark
    # position. At each match, stamp the marker color 4 into the mark positions.
    for r in range(H - th + 1):
        for c in range(W - tw + 1):
            if r == tr and c == tc:
                continue
            ok = True
            for di, dj, v in key:
                if input_grid[r + di][c + dj] != v:
                    ok = False
                    break
            if not ok:
                continue
            for di, dj in marks:
                if input_grid[r + di][c + dj] != 0:
                    ok = False
                    break
            if not ok:
                continue
            for di, dj in marks:
                T[(r + di, c + dj)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
