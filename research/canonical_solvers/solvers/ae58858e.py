def infer_T(input_grid):
    """Latent mask: cells belonging to 4-connected components of color 2 whose
    size is >= 4 are recolored to 6. Returns dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    seen = set()
    T = {}
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                    continue
                if input_grid[a][b] != 2:
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr, dc in neighbors:
                    stack.append((a + dr, b + dc))
            if len(cells) >= 4:
                for cell in cells:
                    T[cell] = 6
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
