def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    div_col = None
    for c in range(W):
        vals = set(input_grid[r][c] for r in range(H))
        if vals <= {8, 1} and 8 in vals:
            div_col = c
            break

    if div_col is not None:
        bars = []
        for r in range(H):
            s = set(input_grid[r])
            if 8 not in s and s != {bg}:
                fills = [v for v in s if v != 1]
                if fills:
                    bars.append((r, fills[0]))
        bar_color = {r: col for r, col in bars}
        boundary_rows = set()
        for i in range(len(bars) - 1):
            r1, c1 = bars[i]
            r2, c2 = bars[i + 1]
            if c1 != c2 and (r1 + r2) % 2 == 0:
                boundary_rows.add((r1 + r2) // 2)
        T = [[None] * W for _ in range(H)]
        for r in range(H):
            if r in bar_color:
                for c in range(W):
                    T[r][c] = 8 if c == div_col else 1
            elif r in boundary_rows:
                for c in range(W):
                    T[r][c] = 1
            else:
                best, bestd = None, None
                for br, bc in bars:
                    dd = abs(br - r)
                    if bestd is None or dd < bestd:
                        bestd, best = dd, bc
                for c in range(W):
                    T[r][c] = 1 if c == div_col else best
        return T
    else:
        div_row = None
        for r in range(H):
            vals = set(input_grid[r])
            if vals <= {8, 1} and 8 in vals:
                div_row = r
                break
        bars = []
        for c in range(W):
            s = set(input_grid[r][c] for r in range(H))
            if 8 not in s and s != {bg}:
                fills = [v for v in s if v != 1]
                if fills:
                    bars.append((c, fills[0]))
        bar_color = {c: col for c, col in bars}
        boundary_cols = set()
        for i in range(len(bars) - 1):
            c1, k1 = bars[i]
            c2, k2 = bars[i + 1]
            if k1 != k2 and (c1 + c2) % 2 == 0:
                boundary_cols.add((c1 + c2) // 2)
        T = [[None] * W for _ in range(H)]
        for c in range(W):
            if c in bar_color:
                for r in range(H):
                    T[r][c] = 8 if r == div_row else 1
            elif c in boundary_cols:
                for r in range(H):
                    T[r][c] = 1
            else:
                best, bestd = None, None
                for bc, bk in bars:
                    dd = abs(bc - c)
                    if bestd is None or dd < bestd:
                        bestd, best = dd, bk
                for r in range(H):
                    T[r][c] = 1 if r == div_row else best
        return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
