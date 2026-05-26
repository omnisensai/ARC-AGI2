def _components(positions):
    """Group a set of (r,c) into 4-connected components."""
    positions = set(positions)
    comps = []
    while positions:
        seed = next(iter(positions))
        stack = [seed]
        comp = set()
        while stack:
            p = stack.pop()
            if p in comp or p not in positions:
                continue
            comp.add(p)
            r, c = p
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((r + dr, c + dc))
        positions -= comp
        comps.append(comp)
    return comps


def _cell_bands(coords):
    """Given sorted coordinates (rows or cols) of the stamp grid, split into
    contiguous runs (each run is one cell band). Returns list of (start,end)."""
    bands = []
    if not coords:
        return bands
    coords = sorted(coords)
    start = prev = coords[0]
    for v in coords[1:]:
        if v == prev + 1:
            prev = v
        else:
            bands.append((start, prev))
            start = prev = v
    bands.append((start, prev))
    return bands


def infer_T(input_grid):
    """Compute a recolor mask {(r,c): color}.

    Structure: a small 'key' rectangle (cells colored with non-0/non-5 values)
    maps 1:1 onto a large grid of 3x3 '5'-stamps laid out with 1-cell gaps.
    Each stamp is recolored: every 5 -> the key color at the matching grid
    position. The key block itself is left untouched.
    """
    H, W = len(input_grid), len(input_grid[0])

    five_cells = [(r, c) for r in range(H) for c in range(W)
                  if input_grid[r][c] == 5]
    key_cells = [(r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] not in (0, 5)]

    T = {}
    if not five_cells or not key_cells:
        return T

    # Stamp-grid bands: contiguous runs of rows/cols that carry any 5.
    five_rows = sorted({r for r, c in five_cells})
    five_cols = sorted({c for r, c in five_cells})
    row_bands = _cell_bands(five_rows)
    col_bands = _cell_bands(five_cols)

    n_rows = len(row_bands)
    n_cols = len(col_bands)

    # Key block: bounding region of non-0/non-5 cells, read as an n_rows x n_cols
    # array of colors indexed by relative position.
    key_rs = sorted({r for r, c in key_cells})
    key_cs = sorted({c for r, c in key_cells})
    kr0, kc0 = key_rs[0], key_cs[0]
    kh = key_rs[-1] - kr0 + 1
    kw = key_cs[-1] - kc0 + 1

    if kh != n_rows or kw != n_cols:
        return T

    key_grid = [[input_grid[kr0 + i][kc0 + j] for j in range(kw)]
                for i in range(kh)]

    key_set = set(key_cells)

    # Recolor each stamp band according to its grid position.
    for bi, (r0, r1) in enumerate(row_bands):
        for bj, (c0, c1) in enumerate(col_bands):
            color = key_grid[bi][bj]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if input_grid[r][c] == 5 and (r, c) not in key_set:
                        T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
