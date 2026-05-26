def infer_T(input_grid):
    """Latent transformation mask.

    The 5-lines partition the background (0) into several connected
    components. The single smallest 0-component is recolored 7 and the
    single largest 0-component is recolored 8; all other cells stay put.
    """
    H, W = len(input_grid), len(input_grid[0])

    # connected components (4-connectivity) of background color 0
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] == 0 and not seen[sr][sc]:
                stack = [(sr, sc)]
                cells = []
                while stack:
                    r, c = stack.pop()
                    if r < 0 or r >= H or c < 0 or c >= W:
                        continue
                    if seen[r][c] or input_grid[r][c] != 0:
                        continue
                    seen[r][c] = True
                    cells.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                comps.append(cells)

    T = [[None] * W for _ in range(H)]
    if not comps:
        return T

    smallest = min(comps, key=len)
    largest = max(comps, key=len)
    for (r, c) in smallest:
        T[r][c] = 7
    for (r, c) in largest:
        T[r][c] = 8
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
