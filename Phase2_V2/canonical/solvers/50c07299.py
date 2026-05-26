def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    T = {}
    if not cells:
        return T
    color = input_grid[cells[0][0]][cells[0][1]]
    L = len(cells)
    # The foreground is a diagonal line oriented down-left (+1,-1);
    # its head is the topmost (smallest-row) cell.
    head = min(cells, key=lambda rc: rc[0])
    # Erase the original line.
    for (r, c) in cells:
        T[(r, c)] = bg
    # Draw an extension going up-right (-1,+1) of length L+1,
    # starting one step beyond the head.
    hr, hc = head
    for i in range(1, L + 2):
        nr, nc = hr - i, hc + i
        if 0 <= nr < H and 0 <= nc < W:
            T[(nr, nc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
