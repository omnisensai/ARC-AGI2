def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    seen = [[False] * W for _ in range(H)]
    # connected-component cell count -> recolor
    size_to_color = {2: 3, 3: 2, 4: 1}
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or seen[r][c]:
                continue
            comp = []
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < H and 0 <= cc < W) or seen[cr][cc]:
                    continue
                if input_grid[cr][cc] == bg:
                    continue
                seen[cr][cc] = True
                comp.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((cr + dr, cc + dc))
            color = size_to_color.get(len(comp))
            if color is not None:
                for cell in comp:
                    T[cell] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
