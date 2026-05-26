def infer_T(input_grid):
    """Infer a latent transformation mask.

    Structure: one solid block of color 2 (a 2x2 bounding box) plus several
    isolated marker cells of color 5. Each 5 slides toward the block's bounding
    box along the orthogonal/diagonal direction that points at the box, and
    stops in the first cell adjacent to the box (the next step would land inside
    the bounding box). T maps original 5-cells -> 0 (cleared) and the landing
    cells -> 5.
    """
    H, W = len(input_grid), len(input_grid[0])

    block = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]
    fives = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]

    T = {}
    if not block or not fives:
        return T

    r0 = min(r for r, c in block)
    r1 = max(r for r, c in block)
    c0 = min(c for r, c in block)
    c1 = max(c for r, c in block)

    def slide(r, c):
        # direction toward the block's bounding box
        if r < r0:
            dr = 1
        elif r > r1:
            dr = -1
        else:
            dr = 0
        if c < c0:
            dc = 1
        elif c > c1:
            dc = -1
        else:
            dc = 0
        while True:
            nr, nc = r + dr, c + dc
            if r0 <= nr <= r1 and c0 <= nc <= c1:
                break
            r, c = nr, nc
        return (r, c)

    # clear all originals first
    for (r, c) in fives:
        T[(r, c)] = 0
    # then set landing cells (overrides clears where landing == origin)
    for (r, c) in fives:
        nr, nc = slide(r, c)
        T[(nr, nc)] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
