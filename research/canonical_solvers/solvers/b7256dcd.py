def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    SHAPE = 6  # neutral shape color, recolored by adjacent markers

    # connected components of SHAPE cells (4-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == SHAPE and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                                and input_grid[nr][nc] == SHAPE):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    # markers: colored cells that are neither background nor the shape color
    markers = [(r, c) for r in range(H) for c in range(W)
               if input_grid[r][c] != bg and input_grid[r][c] != SHAPE]

    # latent mask: erase each marker; recolor its adjacent shape component to it
    T = {}
    for (mr, mc) in markers:
        color = input_grid[mr][mc]
        T[(mr, mc)] = bg
        target_comp = None
        for comp in comps:
            cset = set(comp)
            if any((mr + dr, mc + dc) in cset
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                target_comp = comp
                break
        if target_comp is not None:
            for (cr, cc) in target_comp:
                T[(cr, cc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
