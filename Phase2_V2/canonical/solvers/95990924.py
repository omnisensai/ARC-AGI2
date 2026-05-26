def infer_T(input_grid):
    """Find each 2x2 block of color 5; mark its four diagonal-corner cells
    (one step outside the block) with colors 1/2/3/4 (TL/TR/BL/BR)."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    blocks = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 5 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if seen[cr][cc] or input_grid[cr][cc] != 5:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((cr + dr, cc + dc))
                rs = [p[0] for p in cells]
                cs = [p[1] for p in cells]
                blocks.append((min(rs), min(cs), max(rs), max(cs)))
    T = {}
    for top, left, bot, right in blocks:
        for mr, mc, color in (
            (top - 1, left - 1, 1),
            (top - 1, right + 1, 2),
            (bot + 1, left - 1, 3),
            (bot + 1, right + 1, 4),
        ):
            if 0 <= mr < H and 0 <= mc < W:
                T[(mr, mc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
