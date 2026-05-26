def _components(grid, H, W, colors):
    """8-connected components of cells whose color is in `colors`."""
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colors and not seen[r][c]:
                stack = [(r, c)]
                cell = []
                seen[r][c] = True
                while stack:
                    y, x = stack.pop()
                    cell.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < H and 0 <= nx < W and grid[ny][nx] in colors and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                out.append(cell)
    return out


def infer_T(input_grid):
    """
    Each 8-walled box contains a partial 2-colored shape. The completed shape is
    symmetric about the box's bounding-box center on both axes. The latent mask
    marks every cell that should become a 2 after 4-fold symmetrization of the
    box's current 2-cells about that center.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for box in _components(input_grid, H, W, {8}):
        rs = [c[0] for c in box]
        cs = [c[1] for c in box]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        twos = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                if input_grid[r][c] == 2]
        if not twos:
            continue
        for (r, c) in twos:
            for rr in (r, r0 + r1 - r):
                for cc in (c, c0 + c1 - c):
                    T[(rr, cc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
