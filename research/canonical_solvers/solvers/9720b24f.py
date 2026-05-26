from collections import Counter, deque


def _background(grid):
    """Background is 0 when present, else the most common color."""
    counts = Counter(v for row in grid for v in row)
    if 0 in counts:
        return 0
    return counts.most_common(1)[0][0]


def _components(grid, bg):
    """8-connected same-color components of all non-background cells."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            col = grid[r][c]
            q = deque([(r, c)])
            cells = []
            while q:
                y, x = q.popleft()
                if (y, x) in seen:
                    continue
                if not (0 <= y < H and 0 <= x < W) or grid[y][x] != col:
                    continue
                seen.add((y, x))
                cells.append((y, x))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    q.append((y + dr, x + dc))
            comps.append((col, cells))
    return comps


def infer_T(input_grid):
    """Latent mask: cells of an 'intruder' component that sits inside a larger
    container component get overwritten with the background color.

    A non-background component is erased when its bounding box is contained
    within the bounding box of a strictly larger component of a different
    color (the container/frame the intruder is sitting inside)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)

    boxes = []
    for col, cells in _components(input_grid, bg):
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        boxes.append((col, set(cells), min(rs), max(rs), min(cs), max(cs), len(cells)))

    T = [[None] * W for _ in range(H)]
    for col, cells, r0, r1, c0, c1, n in boxes:
        contained = False
        for col2, _cells2, R0, R1, C0, C1, n2 in boxes:
            if col2 == col:
                continue
            if n2 > n and R0 <= r0 and r1 <= R1 and C0 <= c0 and c1 <= C1:
                contained = True
                break
        if contained:
            for (r, c) in cells:
                T[r][c] = bg
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
