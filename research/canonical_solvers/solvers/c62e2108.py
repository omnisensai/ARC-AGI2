"""Canonical solver for ARC task c62e2108.

Structure: the grid contains hollow 4x4 square "boxes" (a single non-background,
non-marker color) and 4-cell marker segments of color 1 sitting on the grid
edges. Each marker is perpendicular to the edge it rests on and is aligned (by
its 4-cell span) with exactly one box. The marker means: tile the box pattern
repeatedly, starting phase-anchored at the box, stepping toward that edge until
the edge is reached. The box itself is left in place; the tiled copies fill the
band between the box and the edge.

infer_T computes a latent mask {(r,c): color} of every cell that a tiling ray
overwrites. apply_T copies the input and writes only those masked cells.
"""

from collections import deque

MARKER = 1
BG = 0


def _components(grid):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v == BG or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                a, b = q.popleft()
                cells.append((a, b))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        na, nb = a + dr, b + dc
                        if 0 <= na < H and 0 <= nb < W and not seen[na][nb] and grid[na][nb] == v:
                            seen[na][nb] = True
                            q.append((na, nb))
            comps.append((v, cells))
    return comps


def infer_T(grid):
    H, W = len(grid), len(grid[0])
    comps = _components(grid)

    boxes = []     # (color, r0, c0, size, pattern)
    markers = []   # (r0, c0, r1, c1) bounding span of a color-1 segment

    for v, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        if v == MARKER:
            markers.append((r0, c0, r1, c1))
        else:
            h = r1 - r0 + 1
            w = c1 - c0 + 1
            if h == w:  # a square box
                pat = [[grid[r0 + i][c0 + j] for j in range(w)] for i in range(h)]
                boxes.append((v, r0, c0, h, pat))

    T = {}

    def stamp(box, base_r, base_c):
        """Stamp one box copy whose top-left maps to (base_r, base_c)."""
        color, _, _, size, pat = box
        for i in range(size):
            for j in range(size):
                rr, cc = base_r + i, base_c + j
                if 0 <= rr < H and 0 <= cc < W and pat[i][j] != BG:
                    T[(rr, cc)] = pat[i][j]

    for mr0, mc0, mr1, mc1 in markers:
        vertical = (mc0 == mc1)  # marker spans rows in a single column -> left/right edge
        # Determine tiling direction (dr, dc) pointing from box toward the edge.
        if vertical:
            # left edge (col 0) -> step left; right edge -> step right
            step = (0, -1) if mc0 == 0 else (0, 1)
        else:
            # top edge (row 0) -> step up; bottom edge -> step down
            step = (-1, 0) if mr0 == 0 else (1, 0)

        # Find the box aligned with this marker.
        target = None
        for box in boxes:
            _, br0, bc0, size, _ = box
            if vertical:
                if br0 == mr0 and (br0 + size - 1) == mr1:
                    target = box
                    break
            else:
                if bc0 == mc0 and (bc0 + size - 1) == mc1:
                    target = box
                    break
        if target is None:
            continue

        # The marker itself is consumed: erase it to background.
        for r in range(mr0, mr1 + 1):
            for c in range(mc0, mc1 + 1):
                T[(r, c)] = BG

        _, br0, bc0, size, _ = target
        dr, dc = step
        # Tile starting at the box itself, stepping toward the edge, until the
        # whole copy is outside the grid.
        k = 0
        while True:
            base_r = br0 + dr * size * k
            base_c = bc0 + dc * size * k
            # stop when the copy is fully outside the grid
            if base_r + size - 1 < 0 or base_r > H - 1 or base_c + size - 1 < 0 or base_c > W - 1:
                break
            stamp(target, base_r, base_c)
            k += 1

    return T


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
