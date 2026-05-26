def infer_T(input_grid):
    """A diagonal trail of 1s is a ball travelling diagonally. It continues past
    its head in the same direction, passing straight through color-3 walls
    (transparent) and reflecting off color-2 walls. The latent mask T marks every
    cell along the continued bounced trajectory that should become a 1."""
    H, W = len(input_grid), len(input_grid[0])

    ones = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1)
    # Endpoints of the diagonal trail: a 1 with exactly one diagonal 1-neighbour.
    ends = [(r, c) for (r, c) in ones
            if sum(1 for ddr in (-1, 1) for ddc in (-1, 1)
                   if (r + ddr, c + ddc) in ones) == 1]

    T = {}
    if len(ends) != 2:
        return T

    # The tail enters from a grid border; the head is the free endpoint the
    # ball travels away from.
    tail = next((e for e in ends if e[0] in (0, H - 1) or e[1] in (0, W - 1)), ends[0])
    head = ends[0] if ends[1] == tail else ends[1]

    dr = 1 if head[0] > tail[0] else -1
    dc = 1 if head[1] > tail[1] else -1

    # Color 2 cells are reflecting walls; color 3 cells are transparent.
    walls = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2)

    r, c = head
    steps = 0
    while steps < H * W * 4:
        steps += 1
        nr, nc = r + dr, c + dc
        if not (0 <= nr < H and 0 <= nc < W):
            break
        vert_block = (r + dr, c) in walls       # blocked vertically -> flip dr
        horiz_block = (r, c + dc) in walls       # blocked horizontally -> flip dc
        diag_block = (nr, nc) in walls           # corner -> flip both
        if vert_block and horiz_block:
            dr, dc = -dr, -dc
            continue
        if vert_block:
            dr = -dr
            continue
        if horiz_block:
            dc = -dc
            continue
        if diag_block:
            dr, dc = -dr, -dc
            continue
        r, c = nr, nc
        T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
