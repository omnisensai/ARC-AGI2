def infer_T(input_grid):
    """Latent mask: each connected non-background bar is recolored by its rank
    in descending length order (longest -> 1, next -> 2, ...)."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if seen[cr][cc] or input_grid[cr][cc] == bg:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                comps.append(cells)

    # rank longest first; deterministic tiebreak by leftmost column
    comps.sort(key=lambda cells: (-len(cells), min(c for _, c in cells)))

    T = [[None] * W for _ in range(H)]
    for i, cells in enumerate(comps):
        color = i + 1
        for (cr, cc) in cells:
            T[cr][cc] = color
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
