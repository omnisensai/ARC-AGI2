"""Canonical latent-T solver for ARC puzzle ecb67b6d.

Rule (inferred from input structure alone):
  The grid contains a background color (the most common color) and a
  foreground color.  The foreground cells form objects under 8-connectivity
  (orthogonal + diagonal adjacency).  An object is "diagonal" if it contains
  a straight diagonal run of three or more consecutive cells (in either the
  NW-SE or NE-SW direction).  Every cell of such a diagonal object is
  recolored to 8; all other cells are left unchanged.

Canonical form:
  solve(grid) = apply_T(grid, infer_T(grid))
  infer_T returns a latent mask {(r,c): new_color} computed from the input;
  apply_T copies the input and overwrites only the masked cells.
"""

NEW_COLOR = 8
DIAG_MIN = 3


def _dims(grid):
    return len(grid), len(grid[0])


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components8(grid, bg):
    """8-connected components of all non-background cells."""
    H, W = _dims(grid)
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            stack = [(r, c)]
            comp = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen:
                    continue
                if not (0 <= a < H and 0 <= b < W):
                    continue
                if grid[a][b] == bg:
                    continue
                seen.add((a, b))
                comp.append((a, b))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((a + dr, b + dc))
            comps.append(comp)
    return comps


def _max_diagonal_run(comp):
    """Longest run of consecutive cells along a diagonal direction."""
    cells = set(comp)
    best = 1 if comp else 0
    for dr, dc in ((1, 1), (1, -1)):
        for r, c in comp:
            # only start counting at the beginning of a diagonal run
            if (r - dr, c - dc) in cells:
                continue
            length = 0
            rr, cc = r, c
            while (rr, cc) in cells:
                length += 1
                rr += dr
                cc += dc
            if length > best:
                best = length
    return best


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color}."""
    bg = _background(input_grid)
    T = {}
    for comp in _components8(input_grid, bg):
        if _max_diagonal_run(comp) >= DIAG_MIN:
            for cell in comp:
                T[cell] = NEW_COLOR
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
