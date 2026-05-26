def infer_T(input_grid):
    """Each colored rectangle is missing one corner cell, which is replaced by an
    8 marker. The marker's corner indicates a diagonal direction; the whole
    rectangle (restored to solid) shifts one cell that way. The latent mask T
    erases every original rectangle footprint and writes every shifted, solid
    rectangle (writes win over erases so overlapping moves are preserved)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = 7
    # group solid cells (non-background, non-marker) by color
    cols = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != 8:
                cols.setdefault(v, []).append((r, c))

    erase = set()
    writes = {}
    for col, cells in cols.items():
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        cellset = set(cells)
        # the marker (8) occupies the rectangle's one missing corner
        missing = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                   if (r, c) not in cellset]
        mr, mc = missing[0]
        dr = 1 if mr == r1 else -1   # marker on bottom row -> move down
        dc = 1 if mc == c1 else -1   # marker on right column -> move right
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                erase.add((r, c))
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W:
                    writes[(nr, nc)] = col

    T = {}
    for cell in erase:
        T[cell] = bg
    for cell, col in writes.items():
        T[cell] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
