from collections import Counter


def infer_T(input_grid):
    """Infer a latent recolor mask.

    The output is a sorted "stacked bar" of the input's color histogram:
    colors ordered by descending frequency are poured into the grid in
    column-major order, filling each column bottom-to-top, left-to-right
    across columns. Each color occupies exactly as many cells as it has in
    the input. T maps every cell whose color must change to its new color.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)

    # deterministic order: descending count, then ascending color value
    order = sorted(counts.keys(), key=lambda v: (-counts[v], v))

    # traversal cells: column-major, bottom-to-top within each column
    cells = [(r, c) for c in range(W) for r in range(H - 1, -1, -1)]

    T = {}
    idx = 0
    for color in order:
        for _ in range(counts[color]):
            r, c = cells[idx]
            if input_grid[r][c] != color:
                T[(r, c)] = color
            idx += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
