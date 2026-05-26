def infer_T(input_grid):
    """Infer a latent fill mask.

    The grid is divided by separator color 5 into rectangular regions. Each
    region contains one colored marker (1..4) on a background of 0. The whole
    region is filled with color (marker + 5): 1->6, 2->7, 3->8, 4->9.
    """
    H, W = len(input_grid), len(input_grid[0])
    SEP = 5
    T = {}  # (r,c) -> new color (None = leave unchanged)

    # Connected components of non-separator cells (4-connectivity) = regions.
    seen = set()
    comps = []
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] == SEP or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            comp = []
            while stack:
                r, c = stack.pop()
                if not (0 <= r < H and 0 <= c < W):
                    continue
                if (r, c) in seen or input_grid[r][c] == SEP:
                    continue
                seen.add((r, c))
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((r + dr, c + dc))
            comps.append(comp)

    # For each region, locate the marker and fill the whole region with marker+5.
    for comp in comps:
        marker = None
        for (r, c) in comp:
            v = input_grid[r][c]
            if v != 0:
                marker = v
                break
        if marker is None:
            continue
        fill = marker + 5
        for (r, c) in comp:
            T[(r, c)] = fill
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), col in T.items():
        if col is not None:
            out[r][c] = col
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
