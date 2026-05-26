def infer_T(input_grid):
    """Latent mask: a 3x3 ring of color 4 around each crossing of a full
    horizontal line and a full vertical line, leaving the center intact."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Full horizontal lines: rows with no background cell.
    h_lines = [r for r in range(H) if all(input_grid[r][c] != bg for c in range(W))]
    # Full vertical lines: columns with no background cell.
    v_lines = [c for c in range(W) if all(input_grid[r][c] != bg for r in range(H))]

    T = {}  # latent transformation mask: {(r, c): new_color}
    for lr in h_lines:
        for lc in v_lines:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue  # keep the intersection cell unchanged
                    nr, nc = lr + dr, lc + dc
                    if 0 <= nr < H and 0 <= nc < W:
                        T[(nr, nc)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
