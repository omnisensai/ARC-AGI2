def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": 3 * H, "w": 3 * W}          # 2x2 -> 6x6 : 3x3 tiling


def apply_T(g, T):
    H, W = len(g), len(g[0])
    out = [[0] * (3 * W) for _ in range(3 * H)]
    for br in range(3):
        tile = g if br % 2 == 0 else [row[::-1] for row in g]   # odd rows mirrored
        for bc in range(3):
            for r in range(H):
                for c in range(W):
                    out[br * H + r][bc * W + c] = tile[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
