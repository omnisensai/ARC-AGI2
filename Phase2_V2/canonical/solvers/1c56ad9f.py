def infer_T(input_grid):
    """Infer a latent transformation mask.

    The grid holds a single lattice shape on a background. Each occupied row of
    the shape is shifted horizontally by a triangle wave of period 4 that is
    anchored at the bottom row of the shape: shift = [0, -1, 0, +1][(r1 - r) % 4]
    where r1 is the shape's bottom row. The returned mask maps every cell that
    changes to its new color (cleared shape cells -> background, shifted cells ->
    shape color).
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    T = {}
    if not cells:
        return (T, bg)

    r0 = min(r for r, c in cells)
    r1 = max(r for r, c in cells)
    PAT = [0, -1, 0, 1]  # triangle wave, anchored at the bottom row

    for r in range(r0, r1 + 1):
        shift = PAT[(r1 - r) % 4]
        # clear every shape cell in this row to background
        for c in range(W):
            if input_grid[r][c] != bg:
                T[(r, c)] = bg
        # place the shifted copy of each shape cell
        for c in range(W):
            if input_grid[r][c] != bg:
                nc = c + shift
                if 0 <= nc < W:
                    T[(r, nc)] = input_grid[r][c]
    return (T, bg)


def apply_T(input_grid, T):
    mask, bg = T
    out = [row[:] for row in input_grid]
    for (r, c), v in mask.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
