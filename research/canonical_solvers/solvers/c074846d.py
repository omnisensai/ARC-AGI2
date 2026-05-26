def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): new_color}.

    Structure: a single pivot cell (color 5) with an attached straight arm of
    color 2 extending in one of the four orthogonal directions. The arm is
    recolored 3 in place, and a new arm of color 2 of the same length grows
    from the pivot in the direction obtained by rotating the arm 90 degrees
    clockwise around the pivot.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    # Locate the pivot (color 5).
    pivot = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 5:
                pivot = (r, c)
                break
        if pivot is not None:
            break
    if pivot is None:
        return T
    pr, pc = pivot

    # Find which orthogonal direction holds the arm of 2's adjacent to pivot.
    arm_dir = None
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = pr + dr, pc + dc
        if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == 2:
            arm_dir = (dr, dc)
            break
    if arm_dir is None:
        return T
    dr, dc = arm_dir

    # Walk the arm to determine its length and mark those cells -> 3.
    length = 0
    r, c = pr + dr, pc + dc
    while 0 <= r < H and 0 <= c < W and input_grid[r][c] == 2:
        T[(r, c)] = 3
        length += 1
        r += dr
        c += dc

    # New direction: rotate the arm direction 90 degrees clockwise (dr,dc)->(dc,-dr).
    ndr, ndc = dc, -dr
    r, c = pr + ndr, pc + ndc
    for _ in range(length):
        if 0 <= r < H and 0 <= c < W:
            T[(r, c)] = 2
        r += ndr
        c += ndc

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
