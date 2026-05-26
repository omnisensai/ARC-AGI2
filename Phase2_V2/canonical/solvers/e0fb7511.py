"""Canonical solver for ARC puzzle e0fb7511.

Rule: background is 1, markers are 0. Group 0-cells into 4-connected
components. Any 0-cell belonging to a component of size >= 2 (i.e. a 0 that
touches another 0 orthogonally) is recolored to 8. Isolated single 0-cells
stay 0.
"""


def infer_T(input_grid):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    marker = 0
    new_color = 8

    seen = set()
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    T = [[None] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != marker or (r, c) in seen:
                continue
            stack = [(r, c)]
            comp = []
            while stack:
                x, y = stack.pop()
                if (x, y) in seen:
                    continue
                if not (0 <= x < H and 0 <= y < W):
                    continue
                if input_grid[x][y] != marker:
                    continue
                seen.add((x, y))
                comp.append((x, y))
                for dr, dc in dirs:
                    stack.append((x + dr, y + dc))
            if len(comp) >= 2:
                for (x, y) in comp:
                    T[x][y] = new_color
    return T


def apply_T(input_grid, T):
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
