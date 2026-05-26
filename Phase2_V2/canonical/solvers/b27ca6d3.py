"""Canonical solver for ARC puzzle b27ca6d3.

Rule: the foreground color (2) appears as scattered cells. Some of those cells
form adjacent pairs (dominoes of exactly two orthogonally connected cells).
Around every such domino, draw a rectangular ring of 3s on the surrounding
background (0) cells (the bounding box of the pair expanded by one in every
direction). Single isolated cells and larger blobs are left untouched.
"""


def _connected_components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen:
                        continue
                    if not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != color:
                        continue
                    seen.add((x, y))
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((x + dx, y + dy))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """Return a latent transformation mask {(r, c): new_color}.

    Computed purely from input structure: find size-2 components of the
    foreground color and mark the surrounding background ring as color 3.
    """
    H, W = len(input_grid), len(input_grid[0])

    # Background = most common color; foreground = the marker color used in
    # the scattered cells (the most common non-background color).
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    fg_counts = {v: n for v, n in counts.items() if v != bg}
    if not fg_counts:
        return {}
    fg = max(fg_counts, key=fg_counts.get)

    T = {}
    for comp in _connected_components(input_grid, fg):
        if len(comp) != 2:
            continue
        comp_set = set(comp)
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1 = min(rs) - 1, max(rs) + 1
        c0, c1 = min(cs) - 1, max(cs) + 1
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if not (0 <= r < H and 0 <= c < W):
                    continue
                if (r, c) in comp_set:
                    continue
                if input_grid[r][c] == bg:
                    T[(r, c)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
