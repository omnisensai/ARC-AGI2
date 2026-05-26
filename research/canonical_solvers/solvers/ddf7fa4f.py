def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Connected components of all non-background cells (4-connectivity).
    visited = [[False] * W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or visited[r][c]:
                continue
            color = input_grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < H and 0 <= cc < W):
                    continue
                if visited[cr][cc] or input_grid[cr][cc] != color:
                    continue
                visited[cr][cc] = True
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((cr + dr, cc + dc))
            components.append((color, cells))

    # The "fill" color is the one forming multi-cell (rectangle) blobs.
    fill = None
    for color, cells in components:
        if len(cells) > 1:
            fill = color
            break

    # Markers: isolated single cells, recorded by their column.
    markers = []        # (column, color)
    rectangles = []     # (cells, col_min, col_max)
    for color, cells in components:
        if color == fill:
            cmin = min(c for _, c in cells)
            cmax = max(c for _, c in cells)
            rectangles.append((cells, cmin, cmax))
        elif len(cells) == 1:
            (mr, mc), = cells
            markers.append((mc, color))

    # Each rectangle adopts the color of the marker whose column lies within
    # the rectangle's column span.
    T = {}
    for cells, cmin, cmax in rectangles:
        chosen = None
        for mc, color in markers:
            if cmin <= mc <= cmax:
                chosen = color
                break
        if chosen is None:
            continue
        for (r, c) in cells:
            T[(r, c)] = chosen
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
