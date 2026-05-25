def infer_T(input_grid):
    """Compute the latent transformation mask T = {(r,c): new_color}.

    Rule: the background is the most common color. Every non-background cell is a
    marker. For each marker, draw a full-length horizontal and vertical line of 1
    through its row/column, set the marker center to 2, and set its four diagonal
    neighbors to 3. Precedence (low -> high): diagonal 3, line 1, center 2.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    markers = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg]

    T = {}
    # 1) diagonal neighbors -> 3 (lowest precedence)
    for (mr, mc) in markers:
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            r, c = mr + dr, mc + dc
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = 3
    # 2) full horizontal/vertical lines through each marker -> 1 (override diagonals)
    for (mr, mc) in markers:
        for c in range(W):
            T[(mr, c)] = 1
        for r in range(H):
            T[(r, mc)] = 1
    # 3) marker centers -> 2 (highest precedence)
    for (mr, mc) in markers:
        T[(mr, mc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
