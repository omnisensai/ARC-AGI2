def infer_T(input_grid):
    """Find hollow rectangular boxes (border color 5) and fill their interior
    cells with a color determined by interior size: side s -> color s+5.
    Returns a latent mask dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    BORDER = 5

    # connected components of border-colored cells (8-connectivity)
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] != BORDER or seen[sr][sc]:
                continue
            stack = [(sr, sc)]
            cells = []
            while stack:
                r, c = stack.pop()
                if not (0 <= r < H and 0 <= c < W) or seen[r][c]:
                    continue
                if input_grid[r][c] != BORDER:
                    continue
                seen[r][c] = True
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((r + dr, c + dc))
            comps.append(cells)

    T = {}
    for cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        # must be a full rectangular ring: every border cell present,
        # every interior cell non-border
        ok = True
        cellset = set(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                on_edge = (r == r0 or r == r1 or c == c0 or c == c1)
                if on_edge and (r, c) not in cellset:
                    ok = False
                if not on_edge and (r, c) in cellset:
                    ok = False
        ih = (r1 - r0 - 1)
        iw = (c1 - c0 - 1)
        if not ok or ih <= 0 or iw <= 0:
            continue
        side = min(ih, iw)
        color = side + 5
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
