"""Canonical latent-T solver for ARC puzzle 7acdf6d3.

Rule: The grid (background 7) contains two non-background colors. One color forms
"marker" cells scattered/lined up across the grid; the other forms one or more
open container outlines (V / triangle / open-top box). Exactly one container has
an enclosed interior whose cell count equals the total number of marker cells.
The transformation fills that container's interior with the marker color and
erases all the marker cells (back to background).

infer_T discovers, for each candidate marker color, the unique container of the
other color whose interior size matches the marker count, then builds the mask:
interior cells -> marker color, marker cells -> background.
"""


def _background(grid):
    cnt = {}
    for row in grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    return max(cnt, key=cnt.get)


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen, out = set(), []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack, comp = [(r, c)], set()
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen:
                        continue
                    if not (0 <= x < H and 0 <= y < W) or grid[x][y] != color:
                        continue
                    seen.add((x, y))
                    comp.add((x, y))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx or dy:
                                stack.append((x + dx, y + dy))
                out.append(comp)
    return out


def _interior(grid, comp, bg):
    """Background cells inside a container outline: a background cell within the
    component bbox that has component cells to its left, to its right (same row)
    and below it (same column) -- i.e. cells cradled by the open shape."""
    rs = [r for r, c in comp]
    cs = [c for r, c in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    region = set()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) in comp or grid[r][c] != bg:
                continue
            left = any((r, cc) in comp for cc in range(c0, c))
            right = any((r, cc) in comp for cc in range(c + 1, c1 + 1))
            below = any((rr, c) in comp for rr in range(r + 1, r1 + 1))
            if left and right and below:
                region.add((r, c))
    return region


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    colors = sorted({v for row in input_grid for v in row if v != bg})

    T = {}
    for marker in colors:
        m_count = sum(row.count(marker) for row in input_grid)
        if m_count == 0:
            continue
        for other in (c for c in colors if c != marker):
            candidates = []
            for comp in _components(input_grid, other):
                region = _interior(input_grid, comp, bg)
                if len(region) == m_count:
                    candidates.append(region)
            if len(candidates) == 1:
                region = candidates[0]
                for (r, c) in region:
                    T[(r, c)] = marker
                for r in range(H):
                    for c in range(W):
                        if input_grid[r][c] == marker:
                            T[(r, c)] = bg
                return T
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
