def infer_T(input_grid):
    """Find each hollow rectangular box (a colored 4-connected outline) and mark
    its interior bg cells: fill with 5 if the interior is a single cell, else 7."""
    H, W = len(input_grid), len(input_grid[0])
    bg = 0
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or seen[r][c]:
                continue
            color = input_grid[r][c]
            comp = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and input_grid[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rs = [p[0] for p in comp]
            cs = [p[1] for p in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            interior = [(ir, ic)
                        for ir in range(r0 + 1, r1)
                        for ic in range(c0 + 1, c1)
                        if input_grid[ir][ic] == bg]
            fill = 5 if len(interior) == 1 else 7
            for (ir, ic) in interior:
                T[(ir, ic)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
