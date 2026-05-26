"""Canonical latent-T solver for ARC puzzle c3fa4749.

Rule (inferred from all train+test pairs):
  The grid contains several large solid rectangular "window" regions, each a
  single block color with a thin foreground figure drawn inside. The figure is
  corrupted by noise; only a few of its cells still show the true foreground
  color (the "seed"). The whole figure must be repaired to a single color.

  - block color X: a >=18-cell solid connected region (its window rectangle is
    found by trimming bbox rows/cols whose block-color fraction drops below 0.5).
  - fill color: the foreground color is the same for every window. It is the
    color present in the largest non-block component of EVERY window, choosing
    the one with the smallest total count (the genuine sparse seed; coincidental
    noise colors common to all windows occur far more often).
  - per window the figure = the connected (8-neighbour) component of non-block
    cells that contains a seed (fill-colored) cell, plus any block-colored cells
    fully enclosed by it.
  - a window is repaired ONLY if its figure enters from exactly ONE of the four
    rectangle borders (a slit). Fully-enclosed "legend" blobs (0 borders) and
    corner-spanning content patches (>=2 borders) are left untouched.

infer_T returns the latent mask {(r,c): new_color}; apply_T overwrites only
those cells.
"""

from collections import deque


def _components(grid, color, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and grid[ny][nx] == color and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def _trimmed_rect(grid, color, comp, th=0.5):
    rs = [y for y, x in comp]
    cs = [x for y, x in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    frow = lambda r: sum(1 for c in range(c0, c1 + 1) if grid[r][c] == color) / (c1 - c0 + 1)
    fcol = lambda c: sum(1 for r in range(r0, r1 + 1) if grid[r][c] == color) / (r1 - r0 + 1)
    changed = True
    while changed and r0 < r1 and c0 < c1:
        changed = False
        if frow(r0) < th:
            r0 += 1; changed = True
        elif frow(r1) < th:
            r1 -= 1; changed = True
        elif fcol(c0) < th:
            c0 += 1; changed = True
        elif fcol(c1) < th:
            c1 -= 1; changed = True
    return r0, r1, c0, c1


def _get_blocks(grid, H, W):
    raw = []
    for color in range(10):
        for comp in _components(grid, color, H, W):
            if len(comp) >= 18:
                raw.append((color, _trimmed_rect(grid, color, comp)))
    # drop rectangles strictly nested inside a larger one
    res = []
    for col, (r0, r1, c0, c1) in raw:
        nested = False
        for col2, (R0, R1, C0, C1) in raw:
            if (col, (r0, r1, c0, c1)) != (col2, (R0, R1, C0, C1)):
                if R0 <= r0 and r1 <= R1 and C0 <= c0 and c1 <= C1 and \
                   (R1 - R0) * (C1 - C0) > (r1 - r0) * (c1 - c0):
                    nested = True
                    break
        if not nested:
            res.append((col, (r0, r1, c0, c1)))
    return res


def _largest_nonblock_comp(grid, color, rect):
    r0, r1, c0, c1 = rect
    nb = set((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
             if grid[r][c] != color)
    seen = set()
    best = []
    for s in nb:
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        cur = []
        while q:
            y, x = q.popleft()
            cur.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    t = (y + dy, x + dx)
                    if t in nb and t not in seen:
                        seen.add(t)
                        q.append(t)
        if len(cur) > len(best):
            best = cur
    return best


def _infer_fill(grid, blocks, H, W):
    bigs = [(col, rect, _largest_nonblock_comp(grid, col, rect)) for col, rect in blocks]
    color_sets = [set(grid[y][x] for y, x in b) for _, _, b in bigs if b]
    if not color_sets:
        return None
    common = set.intersection(*color_sets)
    if not common:
        return None
    totals = {}
    for cand in common:
        totals[cand] = sum(sum(1 for y, x in b if grid[y][x] == cand) for _, _, b in bigs)
    return min(totals, key=totals.get)


def _seed_component(grid, color, rect, fill):
    r0, r1, c0, c1 = rect
    nb = set((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
             if grid[r][c] != color)
    seeds = [(r, c) for r, c in nb if grid[r][c] == fill]
    if not seeds:
        return set()
    seen = set(seeds)
    q = deque(seeds)
    while q:
        y, x = q.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                t = (y + dy, x + dx)
                if t in nb and t not in seen:
                    seen.add(t)
                    q.append(t)
    return seen


def _enclosed_block_cells(grid, color, rect, figure):
    r0, r1, c0, c1 = rect
    blk = set((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if grid[r][c] == color)
    ext = set()
    q = deque()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r in (r0, r1) or c in (c0, c1)) and (r, c) in blk:
                ext.add((r, c))
                q.append((r, c))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t = (y + dy, x + dx)
            if t in blk and t not in ext:
                ext.add(t)
                q.append(t)
    return blk - ext


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    blocks = _get_blocks(input_grid, H, W)
    fill = _infer_fill(input_grid, blocks, H, W)
    if fill is None:
        return T
    for color, rect in blocks:
        r0, r1, c0, c1 = rect
        comp = _seed_component(input_grid, color, rect, fill)
        if not comp:
            continue
        # figure must enter from exactly one rectangle border (a slit window)
        borders = set()
        for r, c in comp:
            if r == r0:
                borders.add('T')
            if r == r1:
                borders.add('B')
            if c == c0:
                borders.add('L')
            if c == c1:
                borders.add('R')
        if len(borders) != 1:
            continue
        cells = set(comp) | _enclosed_block_cells(input_grid, color, rect, comp)
        for r, c in cells:
            T[(r, c)] = fill
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
