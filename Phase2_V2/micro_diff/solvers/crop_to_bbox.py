from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    return {"r0": r0, "c0": c0, "h": r1 - r0 + 1, "w": c1 - c0 + 1}


def apply_T(g, T):
    return [[g[T["r0"] + r][T["c0"] + c] for c in range(T["w"])]
            for r in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
