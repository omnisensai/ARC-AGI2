def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    # Find connected components of color 1 (8-connectivity) forming box borders.
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W and
                                    not seen[nr][nc] and input_grid[nr][nc] == 1):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                comps.append(cells)

    for cells in comps:
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # Find seed color: the unique non-background, non-border cell inside the box.
        seed = None
        for ir in range(r0 + 1, r1):
            for ic in range(c0 + 1, c1):
                v = input_grid[ir][ic]
                if v not in (0, 1):
                    seed = v
        if seed is None:
            continue
        # Fill the box interior with the seed color.
        for ir in range(r0 + 1, r1):
            for ic in range(c0 + 1, c1):
                T[(ir, ic)] = seed
        # Fill the gap in the top border row with the seed color.
        for ic in range(c0, c1 + 1):
            if input_grid[r0][ic] != 1:
                T[(r0, ic)] = seed
        # Add a seed-colored row above the box top, spanning the box width.
        if r0 - 1 >= 0:
            for ic in range(c0, c1 + 1):
                T[(r0 - 1, ic)] = seed
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
