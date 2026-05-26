def infer_T(input_grid):
    """Infer a latent transformation mask.

    Structure: cells colored 2 and cells colored 3 that are orthogonally
    adjacent form a pair. Each such pair collapses into a single 8 placed at
    the 3-cell; the paired 2-cell is cleared to background (0). Isolated 2s
    and 3s (and all other colors) are left untouched.

    Returns a dict {(r, c): new_color} of overwritten cells.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    used = set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 3:
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < H and 0 <= nc < W):
                    continue
                if input_grid[nr][nc] != 2:
                    continue
                if (nr, nc) in used:
                    continue
                # form pair: 3-cell -> 8, 2-cell -> 0
                T[(r, c)] = 8
                T[(nr, nc)] = 0
                used.add((r, c))
                used.add((nr, nc))
                break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
