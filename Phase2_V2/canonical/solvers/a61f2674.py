def _bars(input_grid):
    """Find connected vertical bars of color 5, return list of (cells, height)."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    bars = []
    for c in range(W):
        for r in range(H):
            if input_grid[r][c] == 5 and not seen[r][c]:
                cells = []
                rr = r
                while rr < H and input_grid[rr][c] == 5:
                    seen[rr][c] = True
                    cells.append((rr, c))
                    rr += 1
                bars.append((cells, len(cells)))
    return bars


def infer_T(input_grid):
    """Latent mask: recolor tallest bar of 5s to 1, shortest to 2, others to 0."""
    H, W = len(input_grid), len(input_grid[0])
    bars = _bars(input_grid)
    T = {}
    if not bars:
        return T
    heights = [h for _, h in bars]
    tallest = max(heights)
    shortest = min(heights)
    tall_done = short_done = False
    for cells, h in bars:
        if h == tallest and not tall_done:
            color = 1
            tall_done = True
        elif h == shortest and not short_done:
            color = 2
            short_done = True
        else:
            color = 0
        for (r, c) in cells:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
