from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    col = g[cells[0][0]][cells[0][1]]
    top = min(r for r, c in cells); bottom = max(r for r, c in cells)
    left = min(c for r, c in cells); right = max(c for r, c in cells)
    T = {}
    for r in range(top, bottom):              # above the floor row
        for c in range(left + 1, right):      # between the walls
            if g[r][c] == bg:
                T[(r, c)] = col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
