def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # background = most common color
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Each non-empty column holds one bottom-anchored vertical bar.
    bars = []
    for c in range(W):
        rows = [r for r in range(H) if input_grid[r][c] != bg]
        if rows:
            color = input_grid[rows[0]][c]
            bars.append((c, color, len(rows)))

    T = {}
    if not bars:
        return T

    # New bar sits two columns right of the rightmost existing bar.
    rightmost_col = max(b[0] for b in bars)
    new_col = rightmost_col + 2
    if new_col >= W:
        return T

    # Height = |sum of 8-bar heights - sum of 2-bar heights|.
    sum8 = sum(h for c, col, h in bars if col == 8)
    sum2 = sum(h for c, col, h in bars if col == 2)
    height = abs(sum8 - sum2)

    # Bottom-anchored bar of color 5 in new_col.
    for i in range(height):
        r = H - 1 - i
        if 0 <= r < H:
            T[(r, new_col)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
