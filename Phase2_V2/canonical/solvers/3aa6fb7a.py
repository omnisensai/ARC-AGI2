def infer_T(input_grid):
    """Find each L-tromino of color 8 and mark the missing corner of its
    bounding 2x2 box to be filled with color 1."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] == 8 and not seen[sr][sc]:
                comp = []
                stack = [(sr, sc)]
                while stack:
                    r, c = stack.pop()
                    if not (0 <= r < H and 0 <= c < W):
                        continue
                    if seen[r][c] or input_grid[r][c] != 8:
                        continue
                    seen[r][c] = True
                    comp.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                # An L-tromino is 3 cells filling all but one cell of a 2x2 box.
                if len(comp) == 3:
                    rs = [r for r, _ in comp]
                    cs = [c for _, c in comp]
                    r0, c0 = min(rs), min(cs)
                    if max(rs) - r0 == 1 and max(cs) - c0 == 1:
                        box = [(r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1)]
                        cset = set(comp)
                        missing = [p for p in box if p not in cset]
                        if len(missing) == 1:
                            T[missing[0]] = 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
