def infer_T(input_grid):
    """Infer a latent fill mask {(r,c): color}.

    Each foreground (color-1) shape is a hollow rectangular box. Its hollow
    interior is filled based on the interior side length: odd side -> 7,
    even side -> 2.
    """
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]

    def component(sr, sc):
        cells, stack = [], [(sr, sc)]
        while stack:
            r, c = stack.pop()
            if not (0 <= r < H and 0 <= c < W) or seen[r][c]:
                continue
            if input_grid[r][c] != 1:
                continue
            seen[r][c] = True
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((r + dr, c + dc))
        return cells

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1 and not seen[r][c]:
                cells = component(r, c)
                rs = [y for y, _ in cells]
                cs = [x for _, x in cells]
                r0, r1 = min(rs), max(rs)
                c0, c1 = min(cs), max(cs)
                ih = r1 - r0 - 1
                iw = c1 - c0 - 1
                if ih <= 0 or iw <= 0:
                    continue
                # interior side parity decides fill color
                color = 7 if (ih % 2 == 1) else 2
                for y in range(r0 + 1, r1):
                    for x in range(c0 + 1, c1):
                        if input_grid[y][x] != 1:
                            T[(y, x)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
