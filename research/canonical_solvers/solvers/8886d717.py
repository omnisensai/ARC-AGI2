def infer_T(input_grid):
    """Latent mask. The grid has a full-edge 9-line (top/bottom/left/right) and
    scattered 8 markers living in one of two regions: a 2-coloured blob or the
    7-coloured background. An 8 touching the 2-blob is erased (-> 2). An 8 in the
    7-background is duplicated one cell toward the 9-line."""
    H, W = len(input_grid), len(input_grid[0])
    rows9, cols9 = set(), set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 9:
                rows9.add(r); cols9.add(c)
    if len(rows9) == 1:
        r0 = next(iter(rows9))
        dr, dc = (-1, 0) if r0 == 0 else (1, 0)        # toward top vs bottom
    else:
        c0 = next(iter(cols9))
        dr, dc = (0, -1) if c0 == 0 else (0, 1)        # toward left vs right
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 8:
                continue
            in_two = any(0 <= r+a < H and 0 <= c+b < W and input_grid[r+a][c+b] == 2
                         for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if in_two:
                T[(r, c)] = 2                          # erase 8 inside the 2-blob
            else:
                nr, nc = r + dr, c + dc                 # duplicate toward 9-line
                if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == 7:
                    T[(nr, nc)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
