"""Canonical solver for ARC puzzle 182e5d0f.

Rule
----
The grid contains "measuring-arm" objects. Each object is an 8-connected
blob of color 3 with two color-0 caps that flank one 3 cell on opposite
sides (the "corner"); from that corner a single line of 3s extends
perpendicular to the 0-0 axis and ends near a color-5 marker.

Some of these arms have their 5 marker sitting *orthogonally* against the
tip of the arm (the arm "points at" the 5). Those arms retract: the whole
line of 3s and the old 5 are erased, the corner 3 is kept, and the single
3 cell adjacent to the corner (the first step of the arm, perpendicular to
the 0-0 axis) is turned into the 5 marker.

Arms whose 5 only touches the arm tip diagonally are left untouched, as are
the static "0 3 0 / 3 3 3 3 3" reference arrows that carry no 5 marker.

infer_T returns the latent mask of cell -> new color overwrites; apply_T
copies the input and applies only those overwrites.
"""


def _components(grid, colors, diag):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(H):
        for c in range(W):
            if grid[r][c] in colors and (r, c) not in seen:
                stack = [(r, c)]
                cur = []
                while stack:
                    a, b = stack.pop()
                    if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                        continue
                    if grid[a][b] not in colors:
                        continue
                    seen.add((a, b))
                    cur.append((a, b))
                    for dr, dc in nb:
                        stack.append((a + dr, b + dc))
                out.append(cur)
    return out


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid
    T = {}  # latent mask: (r, c) -> new color

    ortho = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for comp in _components(g, {0, 3, 5}, diag=True):
        c0 = [(r, c) for r, c in comp if g[r][c] == 0]
        c3 = set((r, c) for r, c in comp if g[r][c] == 3)
        c5 = [(r, c) for r, c in comp if g[r][c] == 5]
        if not c5 or not c3:
            continue  # static reference arrows carry no 5 marker
        five = c5[0]

        # corner: a 3 cell flanked by two 0 cells on opposite sides
        corner = None
        c0set = set(c0)
        for (r, c) in c3:
            if ((r - 1, c) in c0set and (r + 1, c) in c0set) or \
               ((r, c - 1) in c0set and (r, c + 1) in c0set):
                corner = (r, c)
                break
        if corner is None:
            continue

        # does the 5 touch any arm-3 orthogonally? if not, leave object alone
        touches_ortho = any((five[0] + dr, five[1] + dc) in c3 for dr, dc in ortho)
        if not touches_ortho:
            continue

        # first arm cell = 3 neighbour of corner perpendicular to the 0-0 axis
        cr, cc = corner
        vertical_axis = (cr - 1, cc) in c0set and (cr + 1, cc) in c0set
        first_arm = None
        if vertical_axis:
            for dc in (1, -1):
                if (cr, cc + dc) in c3:
                    first_arm = (cr, cc + dc)
                    break
        else:
            for dr in (1, -1):
                if (cr + dr, cc) in c3:
                    first_arm = (cr + dr, cc)
                    break
        if first_arm is None:
            continue

        # erase the whole arm (every 3 except the corner) and the old 5
        for cell in c3:
            if cell != corner:
                T[cell] = 7
        T[five] = 7
        # plant the 5 marker on the first arm cell
        T[first_arm] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
