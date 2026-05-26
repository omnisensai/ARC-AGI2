"""Canonical solver for ARC puzzle a04b2602.

Rule: The grid contains solid rectangles of 3s and scattered 2 markers.
A 2 that lies INSIDE the bounding box of a 3-rectangle is a "center".
For every center, draw a 3x3 ring of 1s (its eight neighbors), overwriting
whatever is there (3s or background 0s, and even other non-center 2s), while
the center 2 itself and any other center 2 are preserved. 2s that do not fall
inside any rectangle (background noise) are left untouched.
"""


def rect_bodies(g):
    """Connected components of 3-colored cells (4-connectivity)."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 3 and not seen[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W) or seen[y][x] or g[y][x] != 3:
                        continue
                    seen[y][x] = True
                    cells.append((y, x))
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        stack.append((y + dy, x + dx))
                comps.append(cells)
    return comps


def infer_T(g):
    """Build the latent mask {(r,c): 1} of cells to recolor to 1."""
    H, W = len(g), len(g[0])

    # Centers: 2s lying within the bounding box of some 3-rectangle.
    centers = set()
    for cm in rect_bodies(g):
        rs = [y for y, x in cm]
        cs = [x for y, x in cm]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if g[r][c] == 2:
                    centers.add((r, c))

    # Each center stamps a 3x3 ring of 1s; never overwrite a center cell.
    T = {}
    for (r, c) in centers:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in centers:
                    T[(nr, nc)] = 1
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
