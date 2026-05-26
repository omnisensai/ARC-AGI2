"""Canonical solver for ARC task 97c75046.

Rule: a single marble (color 5) sits apart from a solid staircase/ramp object
(color 0). The marble is pulled under "gravity" toward the object: gravity points
along the dominant axis from the marble to the object's centroid. The marble
slides straight while free; when blocked it rolls diagonally along the staircase
surface (keeping contact with the object). It comes to rest at the last cell on
its trajectory that is orthogonally adjacent to the object. The marble's old cell
becomes background; its resting cell becomes 5.
"""


def _bg(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _find_marble(grid):
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 5:
                return (r, c)
    return None


def infer_T(input_grid):
    """Return latent mask dict {(r, c): new_color} of cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)

    marble = _find_marble(input_grid)
    if marble is None:
        return {}

    # The object = all non-background, non-marble cells (the staircase / ramp).
    obj = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] != bg and input_grid[r][c] != 5
    )
    if not obj:
        return {}

    rs = [r for r, c in obj]
    cs = [c for r, c in obj]
    cr = sum(rs) / len(rs)
    cc = sum(cs) / len(cs)

    r, c = marble
    # Gravity = dominant axis toward the object's centroid.
    if abs(cr - r) >= abs(cc - c):
        gr, gc = (1, 0) if cr > r else (-1, 0)
    else:
        gr, gc = (0, 1) if cc > c else (0, -1)
    # Perpendicular axis used for diagonal rolling.
    pr, pc = gc, gr

    def free(rr, cc_):
        return 0 <= rr < H and 0 <= cc_ < W and (rr, cc_) not in obj

    def diag_contact(rr, cc_):
        return any(
            (rr + a, cc_ + b) in obj
            for a in (-1, 0, 1)
            for b in (-1, 0, 1)
            if (a, b) != (0, 0)
        )

    def orth_contact(rr, cc_):
        return any(
            (rr + a, cc_ + b) in obj
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    # Simulate rolling: straight when free, otherwise roll diagonally along the
    # surface while remaining in contact with the object.
    path = [(r, c)]
    for _ in range(H * W + 10):
        moved = False
        if free(r + gr, c + gc):
            r, c = r + gr, c + gc
            moved = True
        else:
            for s in (1, -1):
                dr, dc = gr + s * pr, gc + s * pc
                if free(r + dr, c + dc) and diag_contact(r + dr, c + dc):
                    r, c = r + dr, c + dc
                    moved = True
                    break
        if not moved:
            break
        if (r, c) in path:
            break
        path.append((r, c))

    # Resting cell = last cell on the path that orthogonally touches the object.
    rest = path[-1]
    for cell in reversed(path):
        if orth_contact(*cell):
            rest = cell
            break

    T = {}
    if rest != marble:
        T[marble] = bg
        T[rest] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
