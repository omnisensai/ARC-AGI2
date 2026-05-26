def infer_T(input_grid):
    """Latent mask: cells of any 1-component that forms a perfect hollow
    rectangle (full rectangular border of 1s, empty interior) -> recolor to 3."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    seen = [[False] * W for _ in range(H)]
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] != 1 or seen[sr][sc]:
                continue
            # connected component of 1s (8-connectivity)
            comp = []
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                if r < 0 or r >= H or c < 0 or c >= W:
                    continue
                if seen[r][c] or input_grid[r][c] != 1:
                    continue
                seen[r][c] = True
                comp.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((r + dr, c + dc))
            rs = [p[0] for p in comp]
            cs = [p[1] for p in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if h < 3 or w < 3:
                continue
            cset = set(comp)
            # perfect hollow rectangle: border all present, interior all empty
            ok = True
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    on_border = (r == r0 or r == r1 or c == c0 or c == c1)
                    if on_border:
                        if (r, c) not in cset:
                            ok = False
                            break
                    else:
                        if (r, c) in cset:
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                for (r, c) in comp:
                    T[(r, c)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
