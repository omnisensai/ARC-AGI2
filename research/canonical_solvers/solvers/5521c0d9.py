def infer_T(input_grid):
    """Each solid rectangular block of a non-background color is translated
    upward by an amount equal to its own height (so its old top row becomes
    its new bottom row). The latent mask T maps cells to their new colors:
    original block cells are cleared to background, shifted cells get the
    block color."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # connected components (4-conn) of equal-colored non-background cells
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or seen[r][c]:
                continue
            color = input_grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < H and 0 <= cc < W):
                    continue
                if seen[cr][cc] or input_grid[cr][cc] != color:
                    continue
                seen[cr][cc] = True
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((cr + dr, cc + dc))
            comps.append((color, cells))

    T = {}
    # clear all original block cells to background first
    for color, cells in comps:
        for r, c in cells:
            T[(r, c)] = bg
    # then draw each block shifted up by its height (overrides clears on overlap)
    for color, cells in comps:
        rows = [r for r, c in cells]
        height = max(rows) - min(rows) + 1
        for r, c in cells:
            nr = r - height
            if 0 <= nr < H:
                T[(nr, c)] = color
    return T, bg


def apply_T(input_grid, T):
    T, bg = T
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
