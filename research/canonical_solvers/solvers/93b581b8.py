def infer_T(input_grid):
    """Compute a latent transformation mask {(r,c): new_color}.

    Structure: the input contains a single 2x2 block of non-zero colors on a
    zero background. Each of the four block cells "shoots" a 2x2 echo of its
    own color diagonally outward through the corner it occupies (TL->down-right,
    TR->down-left, BL->up-right, BR->up-left). The echo is placed two diagonal
    steps away from the source cell and spans a 2x2 region (clipped to grid).
    """
    H, W = len(input_grid), len(input_grid[0])

    # Locate the 2x2 block: four mutually-adjacent non-zero cells.
    br = bc = None
    for r in range(H - 1):
        for c in range(W - 1):
            if (input_grid[r][c] and input_grid[r][c + 1]
                    and input_grid[r + 1][c] and input_grid[r + 1][c + 1]):
                br, bc = r, c

    T = {}
    if br is None:
        return T

    # Each corner cell with its outward diagonal direction.
    corners = [
        (br,     bc,     1,  1),   # TL -> down-right
        (br,     bc + 1, 1, -1),   # TR -> down-left
        (br + 1, bc,    -1,  1),   # BL -> up-right
        (br + 1, bc + 1, -1, -1),  # BR -> up-left
    ]
    for cr, cc, dr, dc in corners:
        color = input_grid[cr][cc]
        # Echo 2x2 begins two diagonal steps out and spans steps 2 and 3.
        for i in (2, 3):
            for j in (2, 3):
                rr, ccl = cr + i * dr, cc + j * dc
                if 0 <= rr < H and 0 <= ccl < W:
                    T[(rr, ccl)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
