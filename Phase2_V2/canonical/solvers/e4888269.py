"""Canonical solver for ARC puzzle e4888269.

Rule: the grid contains a "legend" -- a solid rectangle exactly 2 cells wide
(or 2 cells tall) whose entries form ordered color pairs (from -> to). Reading
the legend rows top-to-bottom (resp. columns left-to-right) yields a sequence of
substitution steps. A color is recolored by applying each step ONCE, in order:
start with the cell color, and for every pair (a, b) in legend order, if the
current value equals a it becomes b. Every non-legend cell whose value is a
legend "from"-key is rewritten with its recolored value; the legend itself and
all other cells are left untouched.
"""

from collections import Counter, deque


def _background(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and grid[ny][nx] != bg:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def _find_legend(grid, bg):
    """Find the legend: a solid 2-wide (or 2-tall) rectangle with >=2 distinct
    colors and the most cells.  Returns (cells_set, ordered_pairs) or None."""
    best = None
    best_size = -1
    for cells in _components(grid, bg):
        ys = [y for y, x in cells]
        xs = [x for y, x in cells]
        r0, r1 = min(ys), max(ys)
        c0, c1 = min(xs), max(xs)
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        if len(cells) != h * w:
            continue  # not a solid filled rectangle
        if not ((w == 2 and h >= 2) or (h == 2 and w >= 2)):
            continue
        colors = {grid[y][x] for y, x in cells}
        if len(colors) < 2:
            continue  # monochrome block is not a legend
        if len(cells) > best_size:
            best_size = len(cells)
            best = (r0, c0, h, w)
    if best is None:
        return None
    r0, c0, h, w = best
    cellset = {(r0 + i, c0 + j) for i in range(h) for j in range(w)}
    pairs = []
    if w == 2:
        for i in range(h):
            pairs.append((grid[r0 + i][c0], grid[r0 + i][c0 + 1]))
    else:  # h == 2
        for j in range(w):
            pairs.append((grid[r0][c0 + j], grid[r0 + 1][c0 + j]))
    return cellset, pairs


def _recolor(value, pairs):
    """Apply each legend pair once, in order."""
    v = value
    for a, b in pairs:
        if v == a:
            v = b
    return v


def infer_T(input_grid):
    """Latent transformation mask: dict {(r,c): new_color} for cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    found = _find_legend(input_grid, bg)
    T = {}
    if found is None:
        return T
    legend_cells, pairs = found
    from_keys = {a for a, _ in pairs}
    for r in range(H):
        for c in range(W):
            if (r, c) in legend_cells:
                continue
            v = input_grid[r][c]
            if v in from_keys:
                nv = _recolor(v, pairs)
                if nv != v:
                    T[(r, c)] = nv
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
