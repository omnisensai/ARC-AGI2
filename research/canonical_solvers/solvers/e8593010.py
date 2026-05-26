def infer_T(input_grid):
    """Infer a latent transformation mask {(r,c): new_color}.

    The grid is background 5 with scattered marker color 0. Each
    4-connected component of 0s is recolored based on its size:
    the component is mapped to a color so that smaller components get a
    higher color index. Observed mapping from structure:
        size 1 -> 3, size 2 -> 2, size 3 -> 1
    i.e. new_color = 4 - size (for the sizes that occur).
    """
    H, W = len(input_grid), len(input_grid[0])
    marker = 0
    seen = set()
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == marker and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen:
                        continue
                    if not (0 <= x < H and 0 <= y < W):
                        continue
                    if input_grid[x][y] != marker:
                        continue
                    seen.add((x, y))
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((x + dx, y + dy))
                new_color = 4 - len(cells)
                for cell in cells:
                    T[cell] = new_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
