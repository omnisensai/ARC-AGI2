"""Canonical solver for ARC puzzle c97c0139.

Rule: the grid contains straight bars of color 2 (each either a horizontal or a
vertical run). Every bar has odd length L; let R=(L-1)/2 be its radius and let
the bar's center cell be O. A diamond (L1 ball) of radius R centered at O is
drawn in color 8, but only on the cells that lie OFF the bar's own line
(perpendicular distance p>=1). A cell of the diamond is filled when p+|j|<=R,
where p is the perpendicular distance from the bar line and j is the offset
along the bar direction from the center. Only background (0) cells are painted.
"""


def _bg_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_bars(grid, bg):
    """Return list of bars as (cells, orientation, center, radius)."""
    H, W = len(grid), len(grid[0])
    seen = set()
    bars = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            color = grid[r][c]
            # try horizontal run
            if c + 1 < W and grid[r][c + 1] == color:
                cells = [(r, c)]
                cc = c + 1
                while cc < W and grid[r][cc] == color:
                    cells.append((r, cc))
                    cc += 1
                for cell in cells:
                    seen.add(cell)
                L = len(cells)
                center = (r, c + (L - 1) // 2)
                bars.append((cells, 'h', center, (L - 1) // 2, color))
            # try vertical run
            elif r + 1 < H and grid[r + 1][c] == color:
                cells = [(r, c)]
                rr = r + 1
                while rr < H and grid[rr][c] == color:
                    cells.append((rr, c))
                    rr += 1
                for cell in cells:
                    seen.add(cell)
                L = len(cells)
                center = (r + (L - 1) // 2, c)
                bars.append((cells, 'v', center, (L - 1) // 2, color))
            else:
                seen.add((r, c))
    return bars


def infer_T(input_grid):
    """Compute latent transformation mask: dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg_color(input_grid)
    bars = _find_bars(input_grid, bg)
    T = {}
    for cells, orient, center, R, color in bars:
        cr, cc = center
        for dr in range(-R, R + 1):
            for dc in range(-R, R + 1):
                if abs(dr) + abs(dc) > R:
                    continue
                # perpendicular distance p relative to bar line
                if orient == 'h':
                    p = abs(dr)   # rows are perpendicular
                else:
                    p = abs(dc)   # cols are perpendicular
                if p < 1:
                    continue  # on the bar's own line
                r, c = cr + dr, cc + dc
                if 0 <= r < H and 0 <= c < W and input_grid[r][c] == bg:
                    T[(r, c)] = 8
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
