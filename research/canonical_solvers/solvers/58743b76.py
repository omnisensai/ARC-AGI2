def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    # The 2x2 key block: a 2x2 region whose 4 cells are all distinct, none==8, none==0.
    key = None
    for r in range(H - 1):
        for c in range(W - 1):
            vals = [input_grid[r][c], input_grid[r][c + 1],
                    input_grid[r + 1][c], input_grid[r + 1][c + 1]]
            if all(v not in (0, 8) for v in vals) and len(set(vals)) == 4:
                key = (r, c, vals[0], vals[1], vals[2], vals[3])
                break
        if key:
            break
    if key is None:
        return {}
    kr, kc, tl, tr, bl, br = key
    keyset = {(kr, kc), (kr, kc + 1), (kr + 1, kc), (kr + 1, kc + 1)}

    # Marker color = most common non-0 non-8 color outside the key block.
    counts = {}
    for r in range(H):
        for c in range(W):
            if (r, c) in keyset:
                continue
            v = input_grid[r][c]
            if v not in (0, 8):
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return {}
    marker = max(counts, key=counts.get)

    # Main grid bounding box = rectangle spanned by the 0-background cells.
    rows = [r for r in range(H) if any(input_grid[r][c] == 0 for c in range(W))]
    cols = [c for c in range(W) if any(input_grid[r][c] == 0 for r in range(H))]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    midr = r0 + (r1 - r0 + 1) // 2
    midc = c0 + (c1 - c0 + 1) // 2

    # Latent mask: each marker recolored by which quadrant of the main grid it lies in,
    # using the 2x2 key (top-left/top-right/bottom-left/bottom-right).
    T = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if input_grid[r][c] != marker:
                continue
            top = r < midr
            left = c < midc
            if top and left:
                col = tl
            elif top and not left:
                col = tr
            elif not top and left:
                col = bl
            else:
                col = br
            T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
