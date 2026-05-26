from collections import deque


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cells = []
                while q:
                    cr, cc = q.popleft()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == color and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            q.append((nr, nc))
                comps.append(cells)
    return comps


def _count_holes(cells):
    """Number of background regions fully enclosed within the component's bbox."""
    cellset = set(cells)
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    inbox = set()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) not in cellset:
                inbox.add((r, c))
    seen = set()
    holes = 0
    for cell in inbox:
        if cell in seen:
            continue
        q = deque([cell])
        seen.add(cell)
        touch = False
        while q:
            cr, cc = q.popleft()
            if cr == r0 or cr == r1 or cc == c0 or cc == c1:
                touch = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (cr + dr, cc + dc)
                if nb in inbox and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        if not touch:
            holes += 1
    return holes


# number of enclosed holes -> output color
_HOLE_TO_COLOR = {1: 1, 2: 3, 3: 2, 4: 4}


def infer_T(input_grid):
    """Latent mask: each cell of an 8-component maps to a color decided by the
    component's enclosed-hole count."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    for cells in _components(input_grid, 8):
        holes = _count_holes(cells)
        color = _HOLE_TO_COLOR.get(holes, 8)
        for r, c in cells:
            T[r][c] = color
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
