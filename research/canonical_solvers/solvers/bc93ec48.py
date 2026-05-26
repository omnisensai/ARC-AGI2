"""Canonical solver for ARC puzzle bc93ec48.

Rule: the grid has one colored object touching each of the four corners
(top-left, top-right, bottom-right, bottom-left). Each corner object is copied
(shape and color preserved, no reflection) and overlaid onto the NEXT corner in
clockwise order (TL->TR->BR->BL->TL). The copy is anchored so its bounding box
sits in the destination corner. Originals remain wherever the incoming copy does
not cover them (overlay, not swap).
"""

from collections import deque

BG = 7


def _component_at(grid, sr, sc):
    """8-connected component of grid[sr][sc]'s color starting at (sr,sc)."""
    H, W = len(grid), len(grid[0])
    color = grid[sr][sc]
    seen = {(sr, sc)}
    q = deque([(sr, sc)])
    cells = [(sr, sc)]
    while q:
        r, c = q.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen \
                        and grid[nr][nc] == color:
                    seen.add((nr, nc))
                    q.append((nr, nc))
                    cells.append((nr, nc))
    return color, cells


def infer_T(input_grid):
    """Compute the overwrite mask: {(r,c): new_color}.

    For each corner object, place a copy of it at the next corner clockwise,
    anchored into that corner.
    """
    H, W = len(input_grid), len(input_grid[0])
    corners = {
        'TL': (0, 0),
        'TR': (0, W - 1),
        'BL': (H - 1, 0),
        'BR': (H - 1, W - 1),
    }
    clockwise = {'TL': 'TR', 'TR': 'BR', 'BR': 'BL', 'BL': 'TL'}

    objs = {}
    for name, (r, c) in corners.items():
        if input_grid[r][c] != BG:
            objs[name] = _component_at(input_grid, r, c)

    T = {}
    for src, (color, cells) in objs.items():
        dst = clockwise[src]
        minr = min(x[0] for x in cells)
        maxr = max(x[0] for x in cells)
        minc = min(x[1] for x in cells)
        maxc = max(x[1] for x in cells)
        h = maxr - minr + 1
        w = maxc - minc + 1
        if dst == 'TL':
            base = (0, 0)
        elif dst == 'TR':
            base = (0, W - w)
        elif dst == 'BL':
            base = (H - h, 0)
        else:  # 'BR'
            base = (H - h, W - w)
        for r, c in cells:
            nr = base[0] + (r - minr)
            nc = base[1] + (c - minc)
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
