from collections import Counter


def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure: a full-line separator (row or column of one non-background
    color) divides the grid. Each solid rectangular object block is mirrored
    across the separator, and the strip between the block and its mirror is
    flooded with the separator color. T maps (r, c) -> new color.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    cnt = Counter(v for row in g for v in row)
    bg = cnt.most_common(1)[0][0]

    sep_row = next((r for r in range(H)
                    if len(set(g[r])) == 1 and g[r][0] != bg), None)
    sep_col = next((c for c in range(W)
                    if len(set(g[r][c] for r in range(H))) == 1 and g[0][c] != bg),
                   None)
    if sep_row is not None:
        sep_color = g[sep_row][0]
    elif sep_col is not None:
        sep_color = g[0][sep_col]
    else:
        return {}

    def comps(color):
        seen = set()
        out = []
        for r in range(H):
            for c in range(W):
                if g[r][c] == color and (r, c) not in seen:
                    st = [(r, c)]
                    cells = []
                    while st:
                        y, x = st.pop()
                        if (y, x) in seen or not (0 <= y < H and 0 <= x < W) \
                                or g[y][x] != color:
                            continue
                        seen.add((y, x))
                        cells.append((y, x))
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            st.append((y + dy, x + dx))
                    out.append(cells)
        return out

    # Object blocks: solid filled rectangles (area >= 4) of any non-background,
    # non-separator color. Scattered single-cell "noise" is ignored.
    obj_blocks = []
    for color in cnt:
        if color in (bg, sep_color):
            continue
        for cells in comps(color):
            rs = [y for y, _ in cells]
            xs = [x for _, x in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(xs), max(xs)
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            if len(cells) == area and area >= 4:
                obj_blocks.append((color, r0, r1, c0, c1))

    T = {}
    for color, r0, r1, c0, c1 in obj_blocks:
        if sep_col is not None:
            S = sep_col
            mc0, mc1 = 2 * S - c1, 2 * S - c0
            for r in range(r0, r1 + 1):
                for c in range(mc0, mc1 + 1):
                    if 0 <= c < W:
                        T[(r, c)] = color
                lo = min(c1, mc1) + 1
                hi = max(c0, mc0) - 1
                for c in range(lo, hi + 1):
                    if 0 <= c < W:
                        T[(r, c)] = sep_color
        else:
            S = sep_row
            mr0, mr1 = 2 * S - r1, 2 * S - r0
            for c in range(c0, c1 + 1):
                for r in range(mr0, mr1 + 1):
                    if 0 <= r < H:
                        T[(r, c)] = color
                lo = min(r1, mr1) + 1
                hi = max(r0, mr0) - 1
                for r in range(lo, hi + 1):
                    if 0 <= r < H:
                        T[(r, c)] = sep_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
