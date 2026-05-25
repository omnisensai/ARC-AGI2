def infer_T(input_grid):
    """Find square shapes (side >= 2) and mark their four bounding-box corners
    diagonally-outward: each corner gets a 2 in the cell just outside it
    vertically and the cell just outside it horizontally."""
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    seen = set()
    def comp(sr, sc, col):
        st = [(sr, sc)]
        cells = []
        while st:
            r, c = st.pop()
            if (r, c) in seen or not (0 <= r < H and 0 <= c < W):
                continue
            if input_grid[r][c] != col:
                continue
            seen.add((r, c))
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                st.append((r + dr, c + dc))
        return cells

    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and (r, c) not in seen:
                comps.append(comp(r, c, input_grid[r][c]))

    T = {}
    for cells in comps:
        rs = [a for a, _ in cells]
        cs = [b for _, b in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        # Only square shapes whose side is at least 2 get marked.
        if h != w or h < 2:
            continue
        for (cr, cc, vdr, hdc) in (
            (r0, c0, -1, -1),  # top-left corner
            (r0, c1, -1,  1),  # top-right corner
            (r1, c0,  1, -1),  # bottom-left corner
            (r1, c1,  1,  1),  # bottom-right corner
        ):
            for (mr, mc) in ((cr + vdr, cc), (cr, cc + hdc)):
                if 0 <= mr < H and 0 <= mc < W:
                    T[(mr, mc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
