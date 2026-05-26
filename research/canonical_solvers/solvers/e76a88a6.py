"""Canonical solver for ARC puzzle e76a88a6.

Rule: the grid contains one colored "template" object (a small pattern made of
non-background, non-gray colors) and one or more solid gray (5) rectangular
placeholder blocks of the SAME shape as the template's bounding box. Each gray
block is replaced cell-by-cell with the template pattern.
"""

GRAY = 5


def _components(grid, predicate):
    """4-connected components of cells satisfying predicate(value)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if seen[sr][sc] or not predicate(grid[sr][sc]):
                continue
            cells = []
            stack = [(sr, sc)]
            seen[sr][sc] = True
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and predicate(grid[nr][nc]):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def infer_T(input_grid):
    """Return a latent mask {(r,c): new_color} for gray blocks to repaint."""
    grid = input_grid
    H, W = len(grid), len(grid[0])

    # Background = most common color.
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # Template object: connected component of cells that are not bg and not gray.
    tmpl_comps = _components(grid, lambda v: v != bg and v != GRAY)
    if not tmpl_comps:
        return {}
    template = max(tmpl_comps, key=len)
    tr0, tc0, tr1, tc1 = _bbox(template)
    th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
    # Extract the template pattern (relative coords -> color).
    pattern = {}
    for r in range(tr0, tr1 + 1):
        for c in range(tc0, tc1 + 1):
            pattern[(r - tr0, c - tc0)] = grid[r][c]

    # Gray placeholder blocks: each connected component of gray cells, replaced
    # with the template if its bounding box matches the template shape.
    T = {}
    for comp in _components(grid, lambda v: v == GRAY):
        gr0, gc0, gr1, gc1 = _bbox(comp)
        gh, gw = gr1 - gr0 + 1, gc1 - gc0 + 1
        if gh != th or gw != tw:
            continue
        if len(comp) != gh * gw:
            continue  # must be a solid filled rectangle
        for (dr, dc), color in pattern.items():
            T[(gr0 + dr, gc0 + dc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
