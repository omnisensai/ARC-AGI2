"""Canonical solver for ARC puzzle e509e548.

Each connected component of color 3 is a thin (1-cell-wide) path.
The path is recolored based on its shape topology:
  - if it branches (a T-junction -> 3 endpoints): color 2
  - else a simple open path with exactly one bend (corner): color 1
  - else a simple open path with two bends (corners): color 6
infer_T produces a latent mask {(r,c): new_color}; apply_T overwrites only those cells.
"""

ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAG8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr, dc in DIAG8:
                        stack.append((rr + dr, cc + dc))
                comps.append(cells)
    return comps


def _classify(cells):
    """Return the target color for a path component."""
    cset = set(cells)
    endpoints = 0
    corners = 0
    for (r, c) in cells:
        nbs = [(dr, dc) for dr, dc in ORTHO if (r + dr, c + dc) in cset]
        if len(nbs) == 1:
            endpoints += 1
        elif len(nbs) == 2:
            (a, b), (c2, d) = nbs
            if a != -c2 or b != -d:  # not collinear -> a bend
                corners += 1
    if endpoints >= 3:
        return 2
    if corners >= 2:
        return 6
    return 1


def infer_T(input_grid):
    """Latent transformation mask: {(r,c): new_color}."""
    T = {}
    for cells in _components(input_grid, 3):
        col = _classify(cells)
        for (r, c) in cells:
            T[(r, c)] = col
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
