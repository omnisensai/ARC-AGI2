def infer_T(input_grid):
    """Each '1' marker falls straight down its column, dropping below the
    '5' it rests on, until it lands on the lowest non-empty (floor) cell.
    T maps cells to their new color:
      - the original '1' cell becomes 0 (empty)
      - the landing floor cell (a 5) becomes 1
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for c in range(W):
        for r in range(H):
            if input_grid[r][c] != 1:
                continue
            # find the lowest cell in this column that the 1 falls onto:
            # scan downward from r+1; the 1 keeps falling while cells are 5/1,
            # landing on the bottom-most such cell of the supporting stack.
            land = r
            rr = r + 1
            while rr < H and input_grid[rr][c] in (1, 5):
                land = rr
                rr += 1
            if land != r:
                T[(r, c)] = 0          # vacate original position
                T[(land, c)] = 1       # 1 lands here
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
