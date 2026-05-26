def infer_T(input_grid):
    """Infer the latent transformation mask.

    The grid contains one 2x2 solid block (the anchor) plus several scattered
    single-cell markers on the background. Each marker is pulled into the
    quadrant of the 2x2 block that matches its direction relative to the
    block's center (above/below, left/right), and its original cell is cleared.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Locate the 2x2 solid block of a single non-background color.
    block_color = None
    block_cells = []
    for r in range(H - 1):
        for c in range(W - 1):
            v = input_grid[r][c]
            if v != bg and input_grid[r][c + 1] == v \
                    and input_grid[r + 1][c] == v and input_grid[r + 1][c + 1] == v:
                block_color = v
                block_cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]

    T = {}
    if not block_cells:
        return T

    r0 = min(p[0] for p in block_cells)
    c0 = min(p[1] for p in block_cells)
    cr = r0 + 0.5   # block center row
    cc = c0 + 0.5   # block center col

    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg or v == block_color:
                continue
            # clear the marker's original cell
            T[(r, c)] = bg
            # place it in the quadrant matching its direction from the block
            tr = r0 if r < cr else r0 + 1
            tc = c0 if c < cc else c0 + 1
            T[(tr, tc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
