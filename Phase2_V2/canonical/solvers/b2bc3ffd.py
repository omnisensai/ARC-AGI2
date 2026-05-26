def _components(grid, bg, skip_rows):
    """4-connected components of non-bg cells, excluding skip_rows (the floor)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        if r in skip_rows:
            continue
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < H and 0 <= cc < W):
                    continue
                if cr in skip_rows or seen[cr][cc]:
                    continue
                if grid[cr][cc] != color:
                    continue
                seen[cr][cc] = True
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((cr + dr, cc + dc))
            comps.append((color, cells))
    return comps


def infer_T(input_grid):
    """Latent mask {(r,c): color}: each object floats up by N rows where N is
    its own cell count. The floor row (uniform bottom row) stays put."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Floor = bottom rows that are uniform single non-bg color.
    skip_rows = set()
    for r in range(H):
        rowset = set(input_grid[r])
        if len(rowset) == 1 and bg not in rowset:
            skip_rows.add(r)

    comps = _components(input_grid, bg, skip_rows)

    T = {}
    # First clear all object cells, then place shifted cells.
    for color, cells in comps:
        for (r, c) in cells:
            T[(r, c)] = bg
    for color, cells in comps:
        shift = len(cells)
        for (r, c) in cells:
            nr = r - shift
            if 0 <= nr < H:
                T[(nr, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
