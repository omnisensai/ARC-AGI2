def infer_T(input_grid):
    """Find filled rectangles of non-background color; mark their interior cells
    (cells whose 4 orthogonal neighbors are all the same component) to be cleared.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # connected components (4-connectivity) of each non-bg color
    seen = [[False] * W for _ in range(H)]
    T = [[None] * W for _ in range(H)]
    for r0 in range(H):
        for c0 in range(W):
            if seen[r0][c0] or input_grid[r0][c0] == bg:
                continue
            color = input_grid[r0][c0]
            comp = []
            stack = [(r0, c0)]
            seen[r0][c0] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] \
                            and input_grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            cells = set(comp)
            # interior = cells whose all 8 neighbors are in the component
            for (r, c) in comp:
                interior = True
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) not in cells:
                            interior = False
                            break
                    if not interior:
                        break
                if interior:
                    T[r][c] = bg
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
