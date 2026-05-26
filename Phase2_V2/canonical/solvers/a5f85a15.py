def infer_T(input_grid):
    """Diagonal chains of colored cells run down-right (successor = (r+1,c+1)).
    Within each chain, starting at its head (no predecessor up-left), every
    cell at an odd position gets recolored to 4; even positions stay.
    Returns a latent mask dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    cells = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] != 0)

    succ = {}
    for (r, c) in cells:
        cand = (r + 1, c + 1)
        if cand in cells:
            succ[(r, c)] = cand
    preds = set(succ.values())
    heads = [cell for cell in cells if cell not in preds]

    T = {}
    for head in heads:
        cur = head
        idx = 0
        while True:
            if idx % 2 == 1:
                T[cur] = 4
            if cur in succ:
                cur = succ[cur]
                idx += 1
            else:
                break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
