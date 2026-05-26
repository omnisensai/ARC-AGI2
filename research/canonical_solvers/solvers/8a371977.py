def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = 0  # the fill color inside each block

    # Find 4-connected components of the bg color; each is one block.
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and input_grid[nr][nc] == bg:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)

    # Block-grid coordinates from distinct top-rows / left-cols of blocks.
    tops = sorted(set(min(cr for cr, cc in cells) for cells in comps))
    lefts = sorted(set(min(cc for cr, cc in cells) for cells in comps))
    top_idx = {t: i for i, t in enumerate(tops)}
    left_idx = {l: i for i, l in enumerate(lefts)}
    nrows, ncols = len(tops), len(lefts)

    # Border blocks -> 2, interior blocks -> 3.
    T = {}
    for cells in comps:
        t = min(cr for cr, cc in cells)
        l = min(cc for cr, cc in cells)
        br, bc = top_idx[t], left_idx[l]
        on_border = (br == 0 or br == nrows - 1 or bc == 0 or bc == ncols - 1)
        color = 2 if on_border else 3
        for (cr, cc) in cells:
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
