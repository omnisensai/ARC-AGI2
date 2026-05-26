"""Canonical solver for ARC puzzle c97c0139.

Rule: the grid contains straight bars of color 2 (each either a horizontal or a
vertical run) spanning positions a..b along its axis. On BOTH sides of the bar
(perpendicular distance p = 1, 2, ...) color 8 is drawn, with the along-axis
extent shrinking by p from each end: at distance p the 8s cover the along-axis
range [a+p, b-p]. This produces a symmetric double-triangle (diamond) fan.
Only background cells are painted.
"""


def _bg_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_bars(grid, bg):
    """Return list of bars as (orientation, fixed_coord, a, b).

    For 'h' bars fixed_coord is the row, a..b the column span.
    For 'v' bars fixed_coord is the col, a..b the row span.
    """
    H, W = len(grid), len(grid[0])
    seen = set()
    bars = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            color = grid[r][c]
            if c + 1 < W and grid[r][c + 1] == color:  # horizontal run
                cc = c
                while cc < W and grid[r][cc] == color:
                    seen.add((r, cc))
                    cc += 1
                bars.append(('h', r, c, cc - 1))
            elif r + 1 < H and grid[r + 1][c] == color:  # vertical run
                rr = r
                while rr < H and grid[rr][c] == color:
                    seen.add((rr, c))
                    rr += 1
                bars.append(('v', c, r, rr - 1))
            else:
                seen.add((r, c))
    return bars


def infer_T(input_grid):
    """Compute latent transformation mask: dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg_color(input_grid)
    bars = _find_bars(input_grid, bg)
    T = {}
    for orient, fixed, a, b in bars:
        p = 1
        while a + p <= b - p:
            for t in range(a + p, b - p + 1):
                for sign in (-1, 1):
                    if orient == 'h':
                        r, c = fixed + sign * p, t
                    else:
                        r, c = t, fixed + sign * p
                    if 0 <= r < H and 0 <= c < W and input_grid[r][c] == bg:
                        T[(r, c)] = 8
            p += 1
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
