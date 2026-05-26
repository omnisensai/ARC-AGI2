def infer_T(input_grid):
    """Latent mask: locate every plus/cross of color-4 cells (a center whose four
    orthogonal neighbors are all 4) and mark all five cells to be recolored to 8."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    FG = 4          # foreground color forming the shapes
    NEW = 8         # recolor target
    ORTH = ((1, 0), (-1, 0), (0, 1), (0, -1))

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != FG:
                continue
            # plus center: all four orthogonal neighbors in-bounds and also FG
            is_center = True
            for dr, dc in ORTH:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W) or input_grid[nr][nc] != FG:
                    is_center = False
                    break
            if not is_center:
                continue
            T[(r, c)] = NEW
            for dr, dc in ORTH:
                T[(r + dr, c + dc)] = NEW
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
