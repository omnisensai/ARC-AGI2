"""Canonical solver for ARC puzzle 4b6b68e5.

Rule
----
The grid contains several outline shapes drawn in distinct colors, plus
scattered single-cell "marker" dots in various colors. Some outline shapes
form closed loops (their interior is sealed off from the grid border); others
are open. For every CLOSED loop, the interior is flood-filled with the color
of the MAJORITY of marker dots that lie inside it. Every stray marker dot
(anything that is not part of a multi-cell shape) is erased to the background.
Open shapes are left untouched apart from having their stray interior dots
removed.

This is expressed canonically: infer_T builds a latent mask T mapping each
cell that must change to its new color (interior fills + dot erasures), and
apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter


def _components_of_color(grid, color):
    """8-connected connected components of a single color."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < H and 0 <= nx < W
                                    and grid[ny][nx] == color
                                    and not seen[ny][nx]):
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                comps.append(cells)
    return comps


def _interior(grid, wall_cells):
    """Cells sealed off from the border by the given wall (4-connected escape)."""
    H, W = len(grid), len(grid[0])
    wall = set(wall_cells)
    outside = [[False] * W for _ in range(H)]
    stack = []
    for r in range(H):
        for c in range(W):
            if (r == 0 or c == 0 or r == H - 1 or c == W - 1) \
                    and (r, c) not in wall and not outside[r][c]:
                outside[r][c] = True
                stack.append((r, c))
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if (0 <= ny < H and 0 <= nx < W
                    and (ny, nx) not in wall and not outside[ny][nx]):
                outside[ny][nx] = True
                stack.append((ny, nx))
    return [(r, c) for r in range(H) for c in range(W)
            if (r, c) not in wall and not outside[r][c]]


def infer_T(input_grid):
    """Compute the latent transformation mask T = {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = Counter(v for row in input_grid for v in row).most_common(1)[0][0]
    colors = set(v for row in input_grid for v in row) - {bg}

    keep = set()          # cells belonging to multi-cell structural shapes
    fills = {}            # interior cells -> majority dot color

    for col in colors:
        for comp in _components_of_color(input_grid, col):
            # multi-cell components are structural shapes; keep them as-is
            if len(comp) > 1:
                keep.update(comp)
            # any component that encloses an interior is a closed loop: fill it
            inside = _interior(input_grid, comp)
            if inside:
                dots = Counter(input_grid[r][c] for r, c in inside
                               if input_grid[r][c] != bg)
                if dots:
                    fill_color = dots.most_common(1)[0][0]
                    for cell in inside:
                        fills[cell] = fill_color

    T = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if (r, c) in fills:
                # interior of a closed loop -> majority dot color
                if v != fills[(r, c)]:
                    T[(r, c)] = fills[(r, c)]
            elif v != bg and (r, c) not in keep:
                # stray single-cell marker dot -> erase to background
                T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
