def infer_T(input_grid):
    """Infer a latent recolor mask {(r,c): new_color}.

    Each connected component (4-connectivity over non-background cells) is made
    of exactly two non-background colors. Within each component, swap those two
    colors.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == bg or seen[r][c]:
                continue
            comp = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and input_grid[nr][nc] != bg):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            colorset = set(input_grid[cr][cc] for cr, cc in comp)
            if len(colorset) != 2:
                continue
            a, b = tuple(colorset)
            swap = {a: b, b: a}
            for cr, cc in comp:
                T[(cr, cc)] = swap[input_grid[cr][cc]]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
