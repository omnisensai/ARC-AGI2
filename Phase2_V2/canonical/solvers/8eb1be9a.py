def infer_T(input_grid):
    """Latent mask: the input has a contiguous horizontal band of non-empty rows
    (the only rows containing a non-zero color). That band is the vertical
    repeating tile (period = band height). Build a mask that fills every row
    OUTSIDE the band with the band's pattern, phase-aligned so the band stays at
    its original rows: out_row[r] = band_row[(r - r0) mod period]."""
    H, W = len(input_grid), len(input_grid[0])
    band_rows = [r for r in range(H) if any(input_grid[r][c] != 0 for c in range(W))]
    T = [[None] * W for _ in range(H)]
    if not band_rows:
        return T
    r0 = band_rows[0]
    period = len(band_rows)
    for r in range(H):
        if r in band_rows:
            continue
        src = band_rows[(r - r0) % period]
        for c in range(W):
            T[r][c] = input_grid[src][c]
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
