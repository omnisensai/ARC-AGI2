def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Box: hollow rectangle frame drawn in color 1
    frame_color = 1
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == frame_color]
    if not cells:
        return {}
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    # Legend: single colored marker cells outside the box (a top-left diagonal run),
    # ordered by their diagonal position (r+c). This gives the ring color sequence.
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg or v == frame_color:
                continue
            if r0 <= r <= r1 and c0 <= c <= c1:
                continue
            markers.append((r, c, v))
    markers.sort(key=lambda x: (x[0] + x[1], x[0]))
    legend = [v for _, _, v in markers]

    # Fill the box interior with concentric rectangular rings. Ring depth d (0 at the
    # outermost interior border) takes legend[d]; the last legend color fills the center.
    T = {}
    inner_r0, inner_r1 = r0 + 1, r1 - 1
    inner_c0, inner_c1 = c0 + 1, c1 - 1
    for r in range(inner_r0, inner_r1 + 1):
        for c in range(inner_c0, inner_c1 + 1):
            depth = min(r - inner_r0, inner_r1 - r, c - inner_c0, inner_c1 - c)
            idx = depth if depth < len(legend) else len(legend) - 1
            T[(r, c)] = legend[idx]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
